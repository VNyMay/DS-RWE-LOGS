"""Demonstration data for trying out the casebook.

Run from the project folder:

    python seed_data.py            # add the demo records (skips ones already present)
    python seed_data.py --remove   # delete every demo record
    python seed_data.py --reset    # delete the whole local SQLite database, then add demo records

The records describe well-known, real cases. Each one cites the Wikipedia
overview article as its main source: a starting point for research, not a
final academic citation. Every record is flagged ``is_demo`` and labelled
"Demo record" in the interface so it is never confused with a genuine
student submission.
"""

from __future__ import annotations

import argparse
import sys

import config
import database

DEMO_SUBMITTER = "Demo data"

DEMO_EXAMPLES: list[dict] = [
    {
        "title": "Facebook and Cambridge Analytica data scandal",
        "concepts": ['Power', 'Identity', 'Values and ethics'],
        "content_strands": ['Data', 'Media', 'Algorithms'],
        "contexts": ['Political', 'Social'],
        "summary": "Personal data from tens of millions of Facebook users was harvested through a quiz app and used for political profiling without meaningful consent.",
        "technology": "Social media data harvesting",
        "category": "Privacy",
        "subcategory": "Data brokerage",
        "level": "SL",
        "country": "United Kingdom",
        "city": "London",
        "year": 2018,
        "organizations": "Facebook (Meta), Cambridge Analytica, SCL Group",
        "stakeholders": "Facebook users, political campaigns, regulators, journalists, advertisers",
        "affected_groups": "Facebook users whose friends installed the quiz app; voters targeted by political advertising",
        "ethical_issues": ["Privacy", "Consent", "Autonomy and manipulation", "Transparency and accountability"],
        "description": "A personality-quiz app collected data not only from the people who installed it but also from their Facebook friends. The data was passed to Cambridge Analytica, which built psychological profiles for political advertising. Whistleblower reports in 2018 led to public hearings, regulatory investigations and a record fine for Facebook in the United States.",
        "positive_impacts": "The scandal pushed platforms to restrict third-party data access, strengthened public understanding of data rights and accelerated enforcement of data-protection law.",
        "negative_impacts": "Millions of people had their data used without informed consent, and trust in social media platforms and democratic processes was damaged.",
        "ethical_concerns": "Users could not reasonably foresee that a friend's quiz would expose their data. Psychological targeting raises questions about manipulation and the autonomy of voters.",
        "privacy_issues": "Data about friends of app users was collected without their knowledge; retention and onward sharing were not disclosed.",
        "security_issues": "Weak platform controls on third-party developers allowed large-scale extraction of personal data.",
        "environmental_impact": None,
        "legal_issues": "Investigations by the UK Information Commissioner's Office and the US Federal Trade Commission; Facebook agreed to a USD 5 billion settlement in 2019.",
        "conclusion": "The case shows how platform design and business models can undermine consent at scale, and how regulation tends to follow public scandal rather than prevent it.",
        "source_url": "https://en.wikipedia.org/wiki/Facebook%E2%80%93Cambridge_Analytica_data_scandal",
        "additional_sources": "",
        "tags": "data protection, political advertising, consent, whistleblower",
    },
    {
        "title": "Equifax data breach exposes 147 million people",
        "concepts": ['Systems', 'Power', 'Values and ethics'],
        "content_strands": ['Data', 'Computers', 'Networks and the internet'],
        "contexts": ['Economic', 'Social'],
        "summary": "Attackers exploited an unpatched web-application flaw at credit bureau Equifax and stole names, birth dates, social security numbers and more.",
        "technology": "Web application (Apache Struts) and credit databases",
        "category": "Cybersecurity",
        "subcategory": "Data breach",
        "level": "SL",
        "country": "United States",
        "city": "Atlanta",
        "year": 2017,
        "organizations": "Equifax, Apache Software Foundation, US Federal Trade Commission",
        "stakeholders": "Consumers, banks and lenders, regulators, security researchers",
        "affected_groups": "About 147 million people, mostly in the United States, plus consumers in the UK and Canada",
        "ethical_issues": ["Security and safety", "Responsibility and liability", "Transparency and accountability", "Privacy"],
        "description": "A known vulnerability in the Apache Struts framework had a patch available for months, but Equifax did not apply it to a public-facing dispute portal. Attackers used the flaw to access internal systems over several weeks and extracted highly sensitive personal records. Equifax disclosed the breach more than a month after discovering it.",
        "positive_impacts": "The breach led to stronger expectations for patch management, free credit-freeze rights for US consumers and closer regulatory attention to data brokers.",
        "negative_impacts": "Victims faced long-term identity-theft risk that they could not opt out of, because they had never chosen to give Equifax their data.",
        "ethical_concerns": "People whose data was held had no relationship with the company and no way to protect themselves; executives sold shares before disclosure, raising fairness questions.",
        "privacy_issues": "Highly sensitive identifiers that cannot be changed, such as social security numbers, were exposed permanently.",
        "security_issues": "Failure to patch a known vulnerability, expired security certificates that blinded monitoring tools, and slow detection.",
        "environmental_impact": None,
        "legal_issues": "A settlement of up to USD 700 million with US regulators and states; UK fine from the Information Commissioner's Office.",
        "conclusion": "The case demonstrates that basic security hygiene, not exotic attacks, decides most large breaches, and that organisations holding data about non-customers carry special responsibilities.",
        "source_url": "https://en.wikipedia.org/wiki/2017_Equifax_data_breach",
        "additional_sources": "",
        "tags": "breach, patching, identity theft, credit bureau",
    },
    {
        "title": "Clearview AI scrapes billions of faces for police searches",
        "hl_challenge": 'Governance and human rights',
        "intervention": "Regulators in several countries ordered the company to delete residents' data and stop collection; some US states restricted police use of facial recognition.",
        "concepts": ['Power', 'Identity', 'Space', 'Values and ethics'],
        "content_strands": ['Artificial intelligence', 'Data'],
        "contexts": ['Political', 'Social'],
        "summary": "A start-up built a facial-recognition search engine from billions of photos copied from social media without consent and sold access to law enforcement.",
        "technology": "Facial recognition and web scraping",
        "category": "Surveillance",
        "subcategory": "Biometric identification",
        "level": "HL",
        "country": "United States",
        "city": "New York",
        "year": 2020,
        "organizations": "Clearview AI, police departments, data-protection authorities in the EU, UK, Canada and Australia",
        "stakeholders": "People whose photos were scraped, police, social media platforms, civil-liberties organisations",
        "affected_groups": "Anyone with a public photo online; communities over-policed by facial recognition",
        "ethical_issues": ["Surveillance", "Consent", "Privacy", "Bias and discrimination", "Transparency and accountability"],
        "description": "Clearview AI collected images from public websites and social networks to build a searchable face database reportedly containing billions of photos. Police forces could upload a photo of a person and receive matching images and links. Investigative reporting in 2020 revealed the scale of the system and triggered lawsuits, platform cease-and-desist letters and regulatory action in several countries.",
        "positive_impacts": "Law enforcement reported identifying suspects in cases such as child exploitation more quickly.",
        "negative_impacts": "Mass biometric surveillance without consent, risk of false matches, and a chilling effect on public participation.",
        "ethical_concerns": "Turning every public photo into a police-searchable identity record removes practical anonymity in public. Accuracy differences across demographic groups raise fairness concerns.",
        "privacy_issues": "Biometric templates were created from photos people never expected to be used that way, with no ability to opt out.",
        "security_issues": "A large biometric database is a high-value target; the company itself suffered a client-list breach.",
        "environmental_impact": None,
        "legal_issues": "Fines and orders from regulators in Italy, France, the UK, Greece and Australia; a settlement under the Illinois Biometric Information Privacy Act.",
        "conclusion": "This HL case connects surveillance technology to governance and human rights: it shows how a private company can create state-like surveillance capacity faster than law can respond.",
        "source_url": "https://en.wikipedia.org/wiki/Clearview_AI",
        "additional_sources": "",
        "tags": "biometrics, policing, scraping, human rights",
    },
    {
        "title": "UK exam grading algorithm downgrades students in 2020",
        "hl_challenge": 'Governance and human rights',
        "intervention": 'The algorithm was withdrawn within days and grades reverted to teacher assessments; a review recommended human oversight for future automated decisions.',
        "concepts": ['Systems', 'Power', 'Values and ethics'],
        "content_strands": ['Algorithms', 'Data'],
        "contexts": ['Social', 'Political'],
        "summary": "With exams cancelled during the pandemic, an algorithm standardised teacher-predicted grades and lowered many results, disproportionately at state schools.",
        "technology": "Statistical grading algorithm",
        "category": "Education technology",
        "subcategory": "Algorithmic decision-making",
        "level": "HL",
        "country": "United Kingdom",
        "city": None,
        "year": 2020,
        "organizations": "Ofqual, Department for Education, schools and colleges, universities",
        "stakeholders": "Students, teachers, parents, universities, exam regulators, politicians",
        "affected_groups": "A-level and GCSE students, especially high achievers in historically lower-performing schools",
        "ethical_issues": ["Bias and discrimination", "Transparency and accountability", "Digital inequality", "Responsibility and liability"],
        "description": "The regulator Ofqual used a model that combined teachers' predicted grades with each school's historical results to prevent grade inflation. Around 40 percent of A-level grades were lowered from teacher predictions. Because the model leaned on past school performance, capable students in schools with weaker histories were hit hardest. After protests the government abandoned the algorithm and reverted to teacher assessments.",
        "positive_impacts": "The reversal established that automated decisions with major life consequences need appeal routes and human oversight; it became a widely taught case of algorithmic accountability.",
        "negative_impacts": "Students lost university places and experienced significant stress; public trust in the regulator fell.",
        "ethical_concerns": "Judging individuals by the past performance of their school is a form of statistical discrimination. The lack of transparency before results day denied students the chance to challenge the method.",
        "privacy_issues": None,
        "security_issues": None,
        "environmental_impact": None,
        "legal_issues": "Questions were raised under UK data-protection law about automated decision-making; the Information Commissioner's Office engaged with the regulator.",
        "conclusion": "An HL example of governance and inequality: technically defensible statistics produced socially unacceptable outcomes because fairness to individuals was not the objective being optimised.",
        "source_url": "https://en.wikipedia.org/wiki/2020_United_Kingdom_school_exam_grading_controversy",
        "additional_sources": "",
        "tags": "algorithmic fairness, education, pandemic, accountability",
    },
    {
        "title": "Dutch childcare benefits scandal driven by a risk algorithm",
        "hl_challenge": 'Governance and human rights',
        "intervention": 'Compensation for affected families, a parliamentary inquiry, a fine from the data-protection authority and a new government algorithm register.',
        "concepts": ['Power', 'Systems', 'Identity', 'Values and ethics'],
        "content_strands": ['Algorithms', 'Artificial intelligence', 'Data'],
        "contexts": ['Political', 'Economic', 'Social'],
        "summary": "A tax-authority fraud-detection system wrongly flagged tens of thousands of families as fraudsters, with nationality used as a risk indicator.",
        "technology": "Automated fraud-risk scoring",
        "category": "Artificial intelligence",
        "subcategory": "Algorithmic decision-making",
        "level": "HL",
        "country": "Netherlands",
        "city": None,
        "year": 2021,
        "organizations": "Dutch Tax and Customs Administration, Dutch government, Dutch Data Protection Authority",
        "stakeholders": "Families receiving childcare benefits, civil servants, parliament, courts, journalists",
        "affected_groups": "Roughly 26,000 families, many with dual nationality or immigrant backgrounds",
        "ethical_issues": ["Bias and discrimination", "Transparency and accountability", "Responsibility and liability", "Digital inequality"],
        "description": "From around 2013 the tax authority used a self-learning risk model to detect childcare benefit fraud. Having a second nationality was one of the signals. Flagged families had benefits stopped and were ordered to repay large sums, often without being told why. Investigations found institutional bias and a lack of legal safeguards. In 2021 the entire Dutch cabinet resigned over the scandal.",
        "positive_impacts": "The case led to compensation schemes, a national debate on algorithmic transparency and new rules for government use of automated decisions.",
        "negative_impacts": "Families suffered debt, job losses, mental-health harm and in some cases children were taken into care.",
        "ethical_concerns": "Using nationality as a risk factor is discriminatory; opaque scoring made it impossible for people to defend themselves.",
        "privacy_issues": "Personal data including nationality was processed unlawfully, according to the Dutch Data Protection Authority.",
        "security_issues": None,
        "environmental_impact": None,
        "legal_issues": "The Dutch Data Protection Authority fined the tax authority; parliamentary inquiry concluded fundamental principles of the rule of law were violated.",
        "conclusion": "An HL case showing how automation inside government can scale discrimination and evade accountability unless transparency and appeal rights are designed in from the start.",
        "source_url": "https://en.wikipedia.org/wiki/Dutch_childcare_benefits_scandal",
        "additional_sources": "",
        "tags": "government, discrimination, welfare, algorithmic accountability",
    },
    {
        "title": "M-Pesa brings mobile money to millions in Kenya",
        "concepts": ['Change', 'Space', 'Systems'],
        "content_strands": ['Networks and the internet', 'Data'],
        "contexts": ['Economic', 'Social'],
        "summary": "A phone-based payment service let people without bank accounts send, receive and save money, transforming financial inclusion in East Africa.",
        "technology": "Mobile money platform (SMS and USSD based)",
        "category": "Financial technology",
        "subcategory": "Mobile payments",
        "level": "SL",
        "country": "Kenya",
        "city": "Nairobi",
        "year": 2007,
        "organizations": "Safaricom, Vodafone, Central Bank of Kenya",
        "stakeholders": "Unbanked households, small businesses, banks, telecom operators, regulators",
        "affected_groups": "Rural and low-income Kenyans, migrant workers sending money home, small traders",
        "ethical_issues": ["Digital inequality", "Privacy", "Security and safety", "Responsibility and liability"],
        "description": "Launched in 2007, M-Pesa allowed users to deposit cash with local agents and transfer it by text message to anyone with a mobile phone. It spread rapidly because it solved a real problem, sending money to family across the country, cheaply and safely. It grew to include savings, loans, bill payments and merchant payments and became a model copied in many countries.",
        "positive_impacts": "Greater financial inclusion, safer remittances, easier saving, and research linking M-Pesa access to reduced poverty for some households.",
        "negative_impacts": "Dependence on a single dominant operator, fees that fall hardest on small transactions, and the rise of high-interest digital loans.",
        "ethical_concerns": "A private company holds detailed financial data on most of a nation's adults; market dominance can limit choice.",
        "privacy_issues": "Transaction records reveal social networks and spending habits; access by authorities and third parties needs clear limits.",
        "security_issues": "SIM-swap fraud and social-engineering scams target mobile money accounts.",
        "environmental_impact": "Reduced travel for cash transfers; increased demand for phones and agent networks.",
        "legal_issues": "Regulation had to adapt to a telecom offering financial services; interoperability and competition rules followed later.",
        "conclusion": "A largely positive SL case that still shows how inclusion, dependence and data concentration arrive together when a digital system becomes essential infrastructure.",
        "source_url": "https://en.wikipedia.org/wiki/M-Pesa",
        "additional_sources": "",
        "tags": "financial inclusion, mobile payments, development, Africa",
    },
    {
        "title": "TraceTogether contact-tracing data used by police in Singapore",
        "concepts": ['Power', 'Space', 'Values and ethics'],
        "content_strands": ['Data', 'Networks and the internet'],
        "contexts": ['Health', 'Political'],
        "summary": "A pandemic contact-tracing app promised data would only be used for public health, but the government later confirmed police could access it for criminal investigations.",
        "technology": "Bluetooth contact-tracing app and token",
        "category": "Healthcare technology",
        "subcategory": "Public-health surveillance",
        "level": "SL",
        "country": "Singapore",
        "city": "Singapore",
        "year": 2021,
        "organizations": "Government Technology Agency of Singapore, Ministry of Health, Singapore Police Force",
        "stakeholders": "Residents, public-health officials, police, privacy advocates, parliament",
        "affected_groups": "Nearly all residents, since participation became effectively mandatory for entering many venues",
        "ethical_issues": ["Privacy", "Consent", "Transparency and accountability", "Surveillance"],
        "description": "TraceTogether recorded Bluetooth proximity between devices to speed up contact tracing during COVID-19. Officials initially said the data would be used only for contact tracing. In January 2021 the government acknowledged that existing law allowed police to obtain the data for serious crimes, and it had already been used in a murder investigation. Parliament later passed a law restricting police access to a list of serious offences.",
        "positive_impacts": "Faster identification of close contacts and support for reopening the economy during the pandemic.",
        "negative_impacts": "A breach of the public's understanding of the app's purpose, reduced trust in future public-health technology.",
        "ethical_concerns": "Function creep: data collected for one purpose was made available for another. Consent given for health purposes did not cover policing.",
        "privacy_issues": "Proximity logs reveal who met whom; centralised storage created a target for repurposing.",
        "security_issues": "Centralised data stores concentrate risk compared with decentralised designs used elsewhere.",
        "environmental_impact": None,
        "legal_issues": "The COVID-19 (Temporary Measures) (Amendment) Act 2021 limited police use to seven categories of serious crime.",
        "conclusion": "The case shows why purpose limitation must be written into law, not just promised, when a state asks citizens to accept surveillance for a good cause.",
        "source_url": "https://en.wikipedia.org/wiki/TraceTogether",
        "additional_sources": "",
        "tags": "pandemic, contact tracing, purpose limitation, trust",
    },
    {
        "title": "Aadhaar: the world's largest biometric identity system",
        "hl_challenge": 'Global well-being',
        "intervention": 'The Supreme Court limited mandatory use, and exception-handling rules were introduced so that people whose biometrics fail can still receive rations.',
        "concepts": ['Identity', 'Power', 'Systems', 'Change'],
        "content_strands": ['Data', 'Computers'],
        "contexts": ['Political', 'Social', 'Economic'],
        "summary": "India issued over a billion residents a 12-digit ID linked to fingerprints and iris scans, enabling welfare delivery but raising exclusion and surveillance concerns.",
        "technology": "National biometric digital identity",
        "category": "Digital identity",
        "subcategory": "Government ID",
        "level": "HL",
        "country": "India",
        "city": None,
        "year": 2009,
        "organizations": "Unique Identification Authority of India (UIDAI), Government of India, banks and telecom operators",
        "stakeholders": "Residents, welfare recipients, government agencies, private companies, the Supreme Court of India",
        "affected_groups": "Poor and rural residents dependent on subsidised food and benefits; people whose biometrics fail to authenticate",
        "ethical_issues": ["Digital inequality", "Privacy", "Surveillance", "Consent", "Security and safety"],
        "description": "Aadhaar began in 2009 to give every resident a verifiable identity and reduce leakage in welfare programmes. Enrolment captures demographic details, fingerprints and iris scans. Over time Aadhaar became required, or practically required, for benefits, bank accounts and mobile connections. Reports of people denied food rations because of authentication failures, and of data leaks, led to a 2018 Supreme Court ruling that upheld the scheme but limited mandatory use by private companies.",
        "positive_impacts": "Direct benefit transfers reached bank accounts with fewer intermediaries; many people gained a formal identity for the first time.",
        "negative_impacts": "Exclusion of vulnerable people when biometrics fail, risk of profiling as more services link to one number, and data exposure incidents.",
        "ethical_concerns": "Making identity conditional on a working biometric shifts the cost of system failure onto the poorest. Linking many databases to one ID enables surveillance.",
        "privacy_issues": "A single identifier across services allows data to be combined; several leaks of Aadhaar-linked data were reported.",
        "security_issues": "Authentication spoofing and leaked demographic data have been documented; the central database is a critical target.",
        "environmental_impact": None,
        "legal_issues": "The 2017 Puttaswamy judgment recognised privacy as a fundamental right; the 2018 Aadhaar judgment restricted private-sector use.",
        "conclusion": "An HL case linking digital identity to inequality and governance: efficiency gains for the state can coexist with real harm for people the system fails to recognise.",
        "source_url": "https://en.wikipedia.org/wiki/Aadhaar",
        "additional_sources": "",
        "tags": "biometrics, identity, welfare, exclusion, India",
    },
]


def add_demo_records() -> tuple[int, int]:
    """Insert demo records that are not already present. Returns (added, skipped)."""
    existing_titles = {row["title"] for row in database.list_examples(status=None)}
    added = skipped = 0
    for example in DEMO_EXAMPLES:
        if example["title"] in existing_titles:
            skipped += 1
            continue
        record = dict(example)
        record["submitted_by"] = DEMO_SUBMITTER
        database.create_example(record, status="approved", is_demo=True)
        added += 1
    return added, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Add or remove demonstration records.")
    parser.add_argument("--remove", action="store_true", help="delete every demo record and exit")
    parser.add_argument("--reset", action="store_true", help="delete the local SQLite file first, then add demo records")
    args = parser.parse_args(argv)

    if args.reset:
        if config.get_database_url():
            print("--reset only works with the local SQLite database, not DATABASE_URL.")
            return 1
        if config.DATABASE_PATH.exists():
            config.DATABASE_PATH.unlink()
            print(f"Deleted {config.DATABASE_PATH}")

    database.initialize_database()

    if args.remove:
        removed = database.delete_demo_examples()
        print(f"Removed {removed} demonstration record(s).")
        return 0

    added, skipped = add_demo_records()
    print(f"Added {added} demonstration record(s); {skipped} already present.")
    print(f"Database: {config.get_database_url() or config.DATABASE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
