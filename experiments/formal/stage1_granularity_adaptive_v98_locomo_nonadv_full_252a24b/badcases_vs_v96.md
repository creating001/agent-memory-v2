# V98 vs V96 LoCoMo Badcases

Offline diagnostic only: uses labels and judge outputs after prediction. Do not use this file in prediction logic.

- prediction_changed: 534/1540
- changed subset transitions: {'CORRECT->CORRECT': 346, 'CORRECT->WRONG': 46, 'WRONG->CORRECT': 38, 'WRONG->WRONG': 104}

## Losses: v96 CORRECT -> v98 WRONG

### 13fc31c4da9f316b40c10d39
- question: Where did Caroline move from 4 years ago?
- gold: Sweden
- v96: her home country
- v98: home country

### f07b4728d028a1bce5489f14
- question: What did Melanie paint recently?
- gold: sunset
- v96: a sunset
- v98: landscapes and still life

### d3a8d12b5be57abcc6ef6dc6
- question: How many times has Melanie gone to the beach in 2023?
- gold: 2
- v96: 2
- v98: 1

### 97e324be3e76a7dc37e954fd
- question: What types of pottery have Melanie and her kids made?
- gold: bowls, cup
- v96: cup
- v98: pots, cup

### b79bd643671108319bfce3ec
- question: What setback did Melanie face in October 2023?
- gold: She got hurt and had to take a break from pottery.
- v96: Melanie got hurt and had to take a break from pottery.
- v98: Melanie got hurt in September 2023, which led to her taking a break from pottery, an activity she uses for self-expression and peace.

### 340e416afd8bd2c3398d17b6
- question: Why did Jon decide to start his dance studio?
- gold: He lost his job and decided to start his own business to share his passion.
- v96: Jon decided to start his dance studio because dancing has been his passion and escape since childhood, and he wants to share the joy and self-expression it brings with others.
- v98: Jon decided to start his dance studio because dancing has been his passion and escape since childhood, and he wanted to share that joy and create a space for others to express themselves through dance.

### a674db23f228480a6ac66c96
- question: What does Jon's dance make him?
- gold: happy
- v96: most alive, happy, and true to himself
- v98: most alive

### 965980a8fc92af8447abf0e1
- question: How does Gina describe the feeling that dance brings?
- gold: magical
- v96: Gina describes dance as essential to her identity, a source of stress relief, and a way that makes all her worries vanish, giving her a profound and unique emotional feeling.
- v98: Gina describes dance as essential to her identity—like air—and as a stress fix that makes all her worries vanish, giving her a unique and profound emotional release.

### 4d3b88d67b44c6a1ccaeabaa
- question: What does Jon plan to do at the grand opening of his dance studio?
- gold: savor all the good vibes
- v96: Jon plans to host and celebrate the grand opening of his dance studio, making sure everything is perfect and welcoming guests with excitement.
- v98: Jon plans to host the grand opening of his dance studio, welcoming dancers and showcasing his vision as a place of support and mentorship.

### 36e0ab9cd568e5088574aae6
- question: What type of volunteering have John and Maria both done?
- gold: Volunteering at a homeless shelter
- v96: homeless shelter
- v98: John has volunteered as a mentor for a local school, and Maria has volunteered at a homeless shelter. They have not both done the same type of volunteering.

### 814a879f7e6f8da4d042d1f0
- question: What states has Maria vacationed at?
- gold: Oregon, Florida
- v96: Florida, Oregon
- v98: Florida, Spain

### c40fde5951f1c6935056ed96
- question: What area was hit by a flood?
- gold: West County
- v96: West County
- v98: old area

## Gains: v96 WRONG -> v98 CORRECT

### 67f27e2361af6fb035a30c94
- question: Would Melanie be considered a member of the LGBTQ community?
- gold: Likely no, she does not refer to herself as part of it
- v96: unknown
- v98: No

### 09948051ad1179cead77946e
- question: Would Melanie go on another roadtrip soon?
- gold: Likely no; since this one went badly
- v96: The provided information is not enough to determine if Melanie will go on another roadtrip soon.
- v98: No, Melanie would not go on another roadtrip soon.

### 8fd747f0c1272452a98d5170
- question: When did Jon start expanding his studio's social media presence?
- gold: April, 2023
- v96: 2023-05-01
- v98: 2023-04-03

### ff9456ee4d4440403e3411f2
- question: How did Gina promote her clothes store?
- gold: worked with an artist to make unique fashion pieces, made limited-edition sweatshirts, got some new offers and promotions for online store, developed a video presentation showing how to style her pieces
- v96: ad campaign, working with fashion bloggers and influencers, new offers and promotions, building a new website, using social media
- v98: ad campaign, working with fashion bloggers and influencers, offers and promotions, building a new website, collaborating with a local artist, keeping up with fashion trends, building customer relationships

### 57c3fe653fd8d9a2d636457e
- question: What did Gina want her customers to feel in her store?
- gold: cozy and comfortable
- v96: a cool oasis
- v98: Gina wanted her customers to feel like they're in a cool oasis and cozy.

### e21dcb5712d53e2c0962014a
- question: Where is Gina's fashion internship?
- gold: fashion department of an international company
- v96: The provided information is not enough to determine where Gina's fashion internship is located.
- v98: The fashion department of an international company

### b70696c900fd8410819acabc
- question: What people has Maria met and helped while volunteering?
- gold: David, Jean, Cindy, Laura
- v96: Jean, Laura, a man, and someone special (unspecified name)
- v98: Jean, Laura, a man, someone special

### a1592b17423287d9ee57dc37
- question: Who did John go to yoga with?
- gold: Rob
- v96: a colleague
- v98: a colleague (Rob)

### bdbae12e48fe07583e50b3ad
- question: What shelters does Maria volunteer at?
- gold: The homeless shelter, the dog shelter
- v96: ['homeless shelter']
- v98: homeless shelter

### 32e0140f4aeaf8f53b62f055
- question: What attributes describe John?
- gold: Selfless, family-oriented, passionate, rational
- v96: John is described as community-oriented, passionate about improving education and infrastructure, active in fitness (yoga, kickboxing, circuit training, rock climbing, taekwondo), deeply connected to his family, empathetic, resilient, and motivated by personal values and support from loved ones.
- v98: John is described as community-minded, family-oriented, dedicated to personal well-being through exercise, empathetic, proactive in helping others, and passionate about improving education and infrastructure through policymaking.

### 0d7ae1d4468d1f5d668b2978
- question: What activity did John and Max enjoy together last summer?
- gold: Camping
- v96: hiking, swimming, and making great memories
- v98: hiking, swimming, and making great memories during a camping trip

### b040a7da91f43cd6ae3360c2
- question: What are Joanna's hobbies?
- gold: Writing, watchingmovies, exploringnature, hanging withfriends.
- v96: reading, watching movies, exploring nature, writing
- v98: writing, reading, watching movies, exploring nature
