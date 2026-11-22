/*
 * TeamSection.jsx (v3)
 * ---------------------
 * The people behind Dexteria. Plain HTML and CSS (no JavaScript), so it renders on the server.
 *
 * Portraits: every photo is processed by photos/scripts/ so they all share one backdrop,
 * one framing (same head size and eye line) and one black and white grade.
 * Until someone's photo arrives, their card shows the same empty backdrop with their initials.
 *
 * To update a person, edit TEAM below:
 *   name      full name as it should appear
 *   role      one line, or "" while it is not confirmed
 *   photo     file name inside photosPath, or "" while the photo is missing
 *   linkedin, github, email   leave "" to hide that link
 *
 * Phone numbers are deliberately left out: this page is public.
 */
import styles from "./TeamSection.module.css";

const TEAM = [
  {
    name: "Zaina Zayan",
    role: "Cofounder · Mobile & Game Engineer",
    photo: "zaina.webp",
    linkedin: "https://www.linkedin.com/in/zaina-zayan",
    github: "https://github.com/ZainaZayan",
    email: "m.zainazayan@gmail.com",
  },
  {
    name: "Sima Razyeth",
    role: "Cofounder · Backend and Cloud Engineer",
    photo: "sima.webp",
    linkedin: "", // left out on request
    github: "https://github.com/razyeth05-cloud",
    email: "razyeth05@gmail.com",
  },
  {
    name: "Vinuri Nanayakkara",
    role: "Cofounder · Product Engineer",
    photo: "vinuri.webp",
    linkedin: "https://www.linkedin.com/in/vinuri-nanayakkara-5b270b41a",
    github: "https://github.com/vinuri-0210",
    email: "vinuri.20250210@iit.ac.lk",
  },
  {
    name: "Safiya Nazly",
    role: "",
    photo: "safiya.webp",
    linkedin: "https://www.linkedin.com/in/safiya-nazly",
    github: "https://github.com/safiyanaz",
    email: "Safiya.20240516@iit.ac.lk",
  },
  {
    name: "Raiqa Abdul Qadir",
    role: "Cofounder · Mobile & Game Engineer",
    photo: "raiqa.webp",
    linkedin: "https://www.linkedin.com/in/raiqa-abdul-qadir",
    github: "https://github.com/Raiqa-Abdul-Qadir",
    email: "rabdulqadir29@gmail.com",
  },
];

const initials = (name) =>
  name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("");

function Person({ person, photosPath }) {
  const { name, role, photo, linkedin, github, email } = person;
  return (
    <li className={styles.person}>
      <div className={styles.frame}>
        {photo ? (
          <img src={`${photosPath}/${photo}`} alt={`Portrait of ${name}`} width="720" height="900" loading="lazy" decoding="async" />
        ) : (
          <>
            {/* same backdrop as the real portraits, so the row still looks like one set */}
            <img src={`${photosPath}/placeholder.webp`} alt="" width="720" height="900" loading="lazy" decoding="async" />
            <span className={styles.initials} aria-hidden="true">
              {initials(name)}
            </span>
            <span className={styles.pending}>Portrait to come</span>
          </>
        )}
      </div>

      <h3 className={styles.name}>{name}</h3>
      <p className={role ? styles.role : `${styles.role} ${styles.roleMissing}`}>{role || "Role to be confirmed"}</p>

      {(linkedin || github || email) && (
        <ul className={styles.links} aria-label={`${name}, links`}>
          {linkedin && (
            <li>
              <a href={linkedin} target="_blank" rel="noreferrer">
                LinkedIn
              </a>
            </li>
          )}
          {github && (
            <li>
              <a href={github} target="_blank" rel="noreferrer">
                GitHub
              </a>
            </li>
          )}
          {email && (
            <li>
              <a href={`mailto:${email}`}>Email</a>
            </li>
          )}
        </ul>
      )}
    </li>
  );
}

export default function TeamSection({ photosPath = "/team" }) {
  return (
    <section id="team" className={styles.section} aria-labelledby="team-title">
      <div className={styles.inner}>
        <div className={styles.head}>
          <div>
            <p className={styles.kicker}>The team</p>
            <h2 id="team-title" className={styles.title}>
              Five people, one soft ball.
            </h2>
          </div>
          <p className={styles.lead}>
            Dexteria is our Software Development Group Project (SDGP) at IIT Colombo, with the University of
            Westminster.
          </p>
        </div>

        <ul className={styles.grid}>
          {TEAM.map((person) => (
            <Person key={person.name} person={person} photosPath={photosPath} />
          ))}
        </ul>
      </div>
    </section>
  );
}
