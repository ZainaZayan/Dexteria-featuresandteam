/* Both sections use one type family, Archivo (free, Google Fonts), at three widths:
   extra wide for headlines, normal for text, narrow for small labels.
   next/font downloads it at build time and serves it from the site itself.
   The sections read it from the --font-archivo variable set on <html>. */
import { Archivo } from "next/font/google";

const archivo = Archivo({ subsets: ["latin"], axes: ["wdth"], variable: "--font-archivo", display: "swap" });

export const metadata = { title: "Dexteria: Features and Team" };

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={archivo.variable}>
      <body>{children}</body>
    </html>
  );
}
