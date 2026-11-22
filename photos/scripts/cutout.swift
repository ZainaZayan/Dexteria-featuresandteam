// cutout.swift
// Uses Apple's Vision framework (built into macOS, free, runs offline) on one photo:
//   1. cuts the person out of the background  -> a greyscale mask PNG (white = person)
//   2. finds the face and the eyes            -> a small JSON file
// Usage: swift cutout.swift <photo> <mask.png> <face.json>
import CoreImage
import Foundation
import Vision

let args = CommandLine.arguments
guard args.count == 4 else {
    print("usage: swift cutout.swift <photo> <mask.png> <face.json>")
    exit(1)
}
let photoURL = URL(fileURLWithPath: args[1])
guard let image = CIImage(contentsOf: photoURL, options: [.applyOrientationProperty: true]) else {
    print("could not open \(args[1])")
    exit(1)
}

let handler = VNImageRequestHandler(ciImage: image, options: [:])
let personRequest = VNGenerateForegroundInstanceMaskRequest()
let faceRequest = VNDetectFaceLandmarksRequest()
try handler.perform([personRequest, faceRequest])

// 1. mask, same size as the photo
guard let result = personRequest.results?.first else {
    print("no person found")
    exit(1)
}
let maskBuffer = try result.generateScaledMaskForImage(forInstances: result.allInstances, from: handler)
let mask = CIImage(cvPixelBuffer: maskBuffer)
try CIContext().writePNGRepresentation(
    of: mask, to: URL(fileURLWithPath: args[2]), format: .L8,
    colorSpace: CGColorSpaceCreateDeviceGray())

// 2. biggest face. Vision gives 0..1 coordinates with y going UP, so we flip y for the image.
let size = image.extent.size
guard let face = faceRequest.results?.max(by: { $0.boundingBox.width < $1.boundingBox.width }) else {
    print("no face found")
    exit(1)
}
let box = face.boundingBox
func toPixels(_ p: CGPoint) -> [Double] {
    let x = (box.origin.x + p.x * box.width) * size.width
    let y = (1 - (box.origin.y + p.y * box.height)) * size.height
    return [Double(x), Double(y)]
}
func middle(_ region: VNFaceLandmarkRegion2D?) -> [Double]? {
    guard let pts = region?.normalizedPoints, !pts.isEmpty else { return nil }
    let sx = pts.reduce(0) { $0 + $1.x } / CGFloat(pts.count)
    let sy = pts.reduce(0) { $0 + $1.y } / CGFloat(pts.count)
    return toPixels(CGPoint(x: sx, y: sy))
}
var info: [String: Any] = [
    "width": Double(size.width), "height": Double(size.height),
    "face": [Double(box.origin.x * size.width), Double((1 - box.origin.y - box.height) * size.height),
             Double(box.width * size.width), Double(box.height * size.height)],
]
if let l = middle(face.landmarks?.leftEye) { info["leftEye"] = l }
if let r = middle(face.landmarks?.rightEye) { info["rightEye"] = r }
let json = try JSONSerialization.data(withJSONObject: info, options: [.prettyPrinted, .sortedKeys])
try json.write(to: URL(fileURLWithPath: args[3]))
print("ok", args[1])
