/* Demo page: the Features and Team sections as they sit in the Dexteria landing page.
   The space at the top stands in for the hero section, which lives in the main site. */
import FeaturesSection from "@sections/features-v3/FeaturesSection";
import TeamSection from "@sections/team-v3/TeamSection";

export default function Page() {
  return (
    <main>
      <style>{`body{margin:0;background:#F0EBE4;font-family:var(--font-archivo),"Helvetica Neue",Arial,sans-serif}`}</style>
      <div style={{ height: "70vh", display: "grid", placeItems: "center", color: "#4A564D" }}>
        <p>Hero section (from the main site). Scroll down.</p>
      </div>
      <FeaturesSection framesPath="/dexteria/v51" />
      <TeamSection photosPath="/team" />
    </main>
  );
}
