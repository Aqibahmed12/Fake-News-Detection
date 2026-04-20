import csv
import random
import os

random.seed(42)

real_texts = [
    "Scientists at Harvard University published research showing significant improvement in patient outcomes in the journal Nature. This follows months of intensive research and peer review. The findings have been replicated across multiple independent studies. Data was collected over a five-year period from diverse populations.",
    "The United States government announced new climate policy measures on Monday. Experts from around the world have praised the results. The report was published alongside supplementary materials for public review. Data was collected over a five-year period from diverse populations.",
    "Apple reported quarterly earnings of 1.2 billion, beating analyst expectations. This follows months of intensive research and peer review. The findings have been replicated across multiple independent studies. The report was published alongside supplementary materials for public review.",
    "A study from MIT found that a new mechanism for cellular repair offers promising results, according to researchers. Experts from around the world have praised the results. Data was collected over a five-year period from diverse populations. The report was published alongside supplementary materials for public review.",
    "Officials from the United Nations confirmed that the ceasefire occurred following escalating tensions. The findings have been replicated across multiple independent studies. Experts from around the world have praised the results. This follows months of intensive research and peer review.",
    "Health authorities reported 47 new cases of COVID-19 as vaccination continues. Data was collected over a five-year period from diverse populations. The report was published alongside supplementary materials for public review. The findings have been replicated across multiple independent studies.",
    "The central bank raised interest rates by 25 basis points to curb inflation. This follows months of intensive research and peer review. Experts from around the world have praised the results. The report was published alongside supplementary materials for public review.",
    "Lawmakers passed legislation to regulate technology after months of debate. The findings have been replicated across multiple independent studies. Data was collected over a five-year period from diverse populations. Experts from around the world have praised the results.",
    "Researchers discovered that lower carbon emissions than predicted opens new pathways for treatment. Experts from around the world have praised the results. The report was published alongside supplementary materials for public review. This follows months of intensive research and peer review.",
    "The international summit concluded with an agreement on climate change signed by 18 nations. The findings have been replicated across multiple independent studies. Data was collected over a five-year period from diverse populations. The report was published alongside supplementary materials for public review.",
    "Market indices rose 1.2% following positive trade data released this morning. This follows months of intensive research and peer review. Experts from around the world have praised the results. The findings have been replicated across multiple independent studies.",
    "The World Health Organization issued updated guidelines on public health. Data was collected over a five-year period from diverse populations. The report was published alongside supplementary materials for public review. Experts from around the world have praised the results.",
    "Climate scientists warn that rising sea levels will continue if emissions continue at current levels. The findings have been replicated across multiple independent studies. This follows months of intensive research and peer review. Data was collected over a five-year period from diverse populations.",
    "Election officials certified the results showing the incumbent won by 150 votes. Experts from around the world have praised the results. The report was published alongside supplementary materials for public review. The findings have been replicated across multiple independent studies.",
    "The pharmaceutical company announced FDA approval of its new antiviral treatment. Data was collected over a five-year period from diverse populations. This follows months of intensive research and peer review. Experts from around the world have praised the results.",
    "Stanford University researchers have published a comprehensive report on the effects of social media on adolescent mental health. The study followed over three thousand teenagers across five countries for two years. Results indicate a correlation between heavy social media use and increased anxiety levels. Researchers recommend balanced digital consumption and regular offline activities.",
    "The European Central Bank announced a slight reduction in bond purchases as economic indicators signal gradual recovery. Finance ministers from member states expressed cautious optimism during the quarterly summit. Economists note that inflation remains within acceptable ranges. Markets responded positively to the news, with major indices gaining slightly.",
    "A new analysis from Johns Hopkins Bloomberg School of Public Health highlights gaps in rural healthcare access. The study examined data from over two hundred counties across the United States. Researchers found that approximately twelve million people lack adequate access to primary care. Policy recommendations include expanding telehealth services and rural training incentives for physicians.",
    "NASA announced successful testing of a new propulsion system designed for deep space missions. Engineers have been developing the technology for nearly a decade. The system promises significantly reduced travel times to Mars. Mission planners expect the technology to be ready for deployment within the next five years.",
    "The United Nations Environment Programme released its annual report on biodiversity loss. The report warns that extinction rates are accelerating at an unprecedented pace. Over one million species face extinction due to habitat destruction and climate change. International cooperation is identified as essential to reversing these trends.",
]

fake_texts = [
    "SHOCKING: vaccines are actually CAUSED by 5G radiation — government hiding the TRUTH! Share this with everyone you know before it gets deleted!!! The mainstream media will NEVER report this truth! Wake up and do your own research — do not trust the system.",
    "EXPOSED: Secret documents reveal Pfizer has been poisoning water supplies for YEARS! The mainstream media will NEVER report this truth! They are silencing the truth — WE must be the voice of reason!!! Wake up and do your own research — do not trust the system.",
    "Breaking: Bill Gates ARRESTED for mind control experiments - mainstream media covering it up! This has been censored everywhere — spread the word NOW!!! Wake up and do your own research — do not trust the system. They are silencing the truth — WE must be the voice of reason!!!",
    "UNBELIEVABLE! Scientists ADMIT that vaccines cause autism but suppress the EVIDENCE! The mainstream media will NEVER report this truth! Share this with everyone you know before it gets deleted!!! This has been censored everywhere — spread the word NOW!!!",
    "URGENT WARNING: ivermectin linked to autism — BIG PHARMA does not want you to know! Wake up and do your own research — do not trust the system. They are silencing the truth — WE must be the voice of reason!!! This has been censored everywhere — spread the word NOW!!!",
    "This one WEIRD trick the earth is flat — doctors HATE this simple solution! Share this with everyone you know before it gets deleted!!! The mainstream media will NEVER report this truth! Wake up and do your own research — do not trust the system.",
    "CONSPIRACY REVEALED: WHO planned pandemic to control the population! They are silencing the truth — WE must be the voice of reason!!! This has been censored everywhere — spread the word NOW!!! Wake up and do your own research — do not trust the system.",
    "BOMBSHELL: Obama caught on tape admitting election fraud — share before deleted! The mainstream media will NEVER report this truth! Wake up and do your own research — do not trust the system. Share this with everyone you know before it gets deleted!!!",
    "Government INSIDER reveals 5G towers is all a HOAX engineered by New World Order! This has been censored everywhere — spread the word NOW!!! They are silencing the truth — WE must be the voice of reason!!! Share this with everyone you know before it gets deleted!!!",
    "MIRACLE CURE: Simple colloidal silver DESTROYS cancer — FDA tries to BAN it! The mainstream media will NEVER report this truth! Wake up and do your own research — do not trust the system. They are silencing the truth — WE must be the voice of reason!!!",
    "You will NOT believe what George Soros said about chemtrails — DISGUSTING! Share this with everyone you know before it gets deleted!!! This has been censored everywhere — spread the word NOW!!! Wake up and do your own research — do not trust the system.",
    "They do NOT want you to know about this: COVID was engineered proven by secret researchers! The mainstream media will NEVER report this truth! They are silencing the truth — WE must be the voice of reason!!! This has been censored everywhere — spread the word NOW!!!",
    "SCANDAL: Google secretly funding terrorism while covering up effects on YOUR family! Wake up and do your own research — do not trust the system. Share this with everyone you know before it gets deleted!!! The mainstream media will NEVER report this truth!!!",
    "WAKE UP SHEEPLE: fluoride is actually a hoax designed to control us all! This has been censored everywhere — spread the word NOW!!! They are silencing the truth — WE must be the voice of reason!!! Share this with everyone you know before it gets deleted!!!",
    "Deep state EXPOSED: Fauci is behind the pandemic that shocked the world! The mainstream media will NEVER report this truth! Wake up and do your own research — do not trust the system. They are silencing the truth — WE must be the voice of reason!!!",
    "BREAKING!!! 5G towers are secretly being used to beam mind control signals into the brains of the population!!! Governments have been planning this since the 1990s!!! Doctors and scientists who speak out are silenced and de-platformed!!! Share this everywhere before the deep state deletes it!!!",
    "The REAL reason they want you vaccinated is to implant microchips for population control!!! Bill Gates admitted this in a secret meeting that was leaked online!!! The lamestream fake news media refuses to cover this bombshell story!!! Wake up sheeple — your freedom is at stake!!!",
    "EXPOSED: The moon landing was FAKED by Hollywood directors hired by the CIA!!! Newly leaked documents PROVE that NASA has been lying to us for decades!!! Thousands of engineers and scientists are being silenced for speaking the truth!!! Do your own research before it is too late!!!",
    "SHOCKING TRUTH: chemtrails contain dangerous chemicals that are making people SICK!!! The government uses weather modification technology to control crop yields and populations!!! Natural healers have been arrested for exposing the truth!!! Share this with everyone you trust — time is running out!!!",
    "SECRET CURE for cancer has existed since the 1930s but pharmaceutical companies are HIDING it!!! Doctors who try to prescribe the cure are stripped of their licenses!!! Thousands have been healed using suppressed remedies that Big Pharma cannot profit from!!! The truth WILL come out!!!",
]

rows = []
for i in range(750):
    t = real_texts[i % len(real_texts)]
    rows.append({"text": t, "label": 1})

for i in range(750):
    t = fake_texts[i % len(fake_texts)]
    rows.append({"text": t, "label": 0})

random.shuffle(rows)

os.makedirs("data", exist_ok=True)
with open("data/demo_dataset.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["text", "label"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} rows -> data/demo_dataset.csv")
