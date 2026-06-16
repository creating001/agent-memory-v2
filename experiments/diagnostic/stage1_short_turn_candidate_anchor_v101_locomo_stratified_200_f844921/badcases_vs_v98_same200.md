# Badcases vs v98 on LoCoMo stratified 200

- v98 same200: 151/200 = 0.755000
- v101 same200: 144/200 = 0.720000
- delta_vs_v98: -7
- transitions: {'WRONG->WRONG': 40, 'CORRECT->CORRECT': 135, 'CORRECT->WRONG': 16, 'WRONG->CORRECT': 9}
- by_category: {'1': {'name': 'Multi-Hop', 'WRONG->WRONG': 11, 'CORRECT->CORRECT': 32, 'CORRECT->WRONG': 5, 'WRONG->CORRECT': 2}, '2': {'name': 'Temporal Reasoning', 'CORRECT->CORRECT': 36, 'WRONG->WRONG': 10, 'CORRECT->WRONG': 1, 'WRONG->CORRECT': 3}, '3': {'name': 'Open-Domain', 'CORRECT->CORRECT': 27, 'CORRECT->WRONG': 7, 'WRONG->WRONG': 14, 'WRONG->CORRECT': 2}, '4': {'name': 'Single-Hop', 'WRONG->CORRECT': 2, 'CORRECT->CORRECT': 40, 'WRONG->WRONG': 5, 'CORRECT->WRONG': 3}}
- by_route: {'fact_lookup': {'CORRECT->CORRECT': 75, 'WRONG->WRONG': 22, 'CORRECT->WRONG': 11, 'WRONG->CORRECT': 3}, 'list_count': {'CORRECT->CORRECT': 23, 'WRONG->WRONG': 8, 'CORRECT->WRONG': 4, 'WRONG->CORRECT': 3}, 'profile_preference': {'CORRECT->CORRECT': 3}, 'temporal_lookup': {'WRONG->WRONG': 10, 'CORRECT->WRONG': 1, 'CORRECT->CORRECT': 34, 'WRONG->CORRECT': 3}}

## Losses: v98 CORRECT -> v101 WRONG

### Loss 1: 050de4d029518a005ce9e39a (Multi-Hop, list_count)
- question: What activities does Melanie partake in?
- gold: 
- v98: running, playing clarinet, hiking, camping, pottery, painting, participating in a charity race
- v101: running, reading, playing violin, playing clarinet, hiking in mountains, exploring forests, camping, painting, pottery, charity race for mental health

### Loss 2: 0968f8b1c60a55755c7aeccc (Multi-Hop, list_count)
- question: How many times has Joanna's scripts been rejected?
- gold: 
- v98: 2
- v101: 3

### Loss 3: 0f12b20501887ba1ad098125 (Multi-Hop, list_count)
- question: What exercises has John done?
- gold: 
- v98: rock climbing, kickboxing, taekwondo, boot camps, weight training, yoga
- v101: kickboxing, yoga, boot camps, weight training

### Loss 4: 146487c67925ca15d9b78d68 (Multi-Hop, temporal_lookup)
- question: Which of James's family members have visited him in the last year?
- gold: 
- v98: mother, family
- v101: mother

### Loss 5: 181822affe199acc49ef98ee (Multi-Hop, list_count)
- question: Which games have Jolene and her partner played together?
- gold: 
- v98: Detroit, It takes two, Overcooked 2
- v101: Detroit, It takes two, Overcooked 2

### Loss 6: 0bd234ac04c7e45eab9d62ab (Temporal Reasoning, fact_lookup)
- question: Where did Jolene and her partner spend most of September 2023?
- gold: 
- v98: Phuket
- v101: Rio de Janeiro

### Loss 7: 09948051ad1179cead77946e (Open-Domain, fact_lookup)
- question: Would Melanie go on another roadtrip soon?
- gold: 
- v98: No, Melanie would not go on another roadtrip soon.
- v101: The provided information is not enough to determine if Melanie will go on another roadtrip soon.

### Loss 8: 157f0dada26acf0d3e7952bd (Open-Domain, fact_lookup)
- question: What might John's degree be in?
- gold: 
- v98: public policy or urban planning
- v101: The provided information is not enough to determine John's degree field.

### Loss 9: 1ba1789ca790bb6323a5ac22 (Open-Domain, fact_lookup)
- question: What could John do after his basketball career?
- gold: 
- v98: building his brand, pursuing endorsements, supporting youth sports, organizing basketball camps, holding benefit games
- v101: build his brand and make a positive difference off the court

### Loss 10: 230f74ceefa905e34b5735d5 (Open-Domain, fact_lookup)
- question: Is Deborah married?
- gold: 
- v98: Yes, Deborah is married.
- v101: No

### Loss 11: 2c3c412e31749cbb25d23871 (Open-Domain, fact_lookup)
- question: What additional country did James visit during his trip to Canada?
- gold: 
- v98: Greenland
- v101: Nuuk

### Loss 12: 548bc68285642f4459991c2a (Open-Domain, fact_lookup)
- question: What is a prominent charity organization that John might want to work with and why?
- gold: 
- v98: A local organization that helps disadvantaged kids with sports and school
- v101: A local organization that helps disadvantaged kids with sports and school

## Gains: v98 WRONG -> v101 CORRECT

### Gain 1: 0bb99b11d4e9e2211195173a (Multi-Hop, list_count)
- question: What symbols are important to Caroline?
- gold: 
- v98: rainbow flag mural, eagle symbol, poster with themes of freedom and authenticity
- v101: necklace from grandmother in Sweden, hand-painted bowl by a friend, rainbow flag mural, eagle in the mural, drawing symbolizing freedom and authenticity

### Gain 2: 23cab7e7f9f1332e7b350a41 (Multi-Hop, list_count)
- question: Which activity did Sam resume in December 2023 after a long time?
- gold: 
- v98: running
- v101: hiking

### Gain 3: 109edb15a81b883aab67f8ce (Temporal Reasoning, temporal_lookup)
- question: When did Melanie's family go on a roadtrip?
- gold: 
- v98: 2023-10-19
- v101: 2023-10-14 to 2023-10-15

### Gain 4: 1340bc97cd504e993b131b87 (Temporal Reasoning, temporal_lookup)
- question: When did Nate win his third tourney?
- gold: 
- v98: 2022-11-05
- v101: 2022-05-27 to 2022-06-02

### Gain 5: 16d70285e40a99b09091bd7a (Temporal Reasoning, temporal_lookup)
- question: How many weeks passed between Maria adopting Coco and Shadow?
- gold: 
- v98: 2 weeks and 2 days
- v101: 2

### Gain 6: 2245ba33bb4c804acc9e76ea (Open-Domain, fact_lookup)
- question: What is something that Andrew could do to make birdwatching hobby to fit in his city schedule?
- gold: 
- v98: Andrew could use nearby parks or green spaces in the city to do birdwatching, fitting it into his schedule by exploring local areas during breaks or weekends.
- v101: Andrew could make birdwatching fit his city schedule by using nearby parks and green spaces for observation, as he has shown interest in nature and plans to explore such areas despite urban living.

### Gain 7: 29810bc865f064d647127d7e (Open-Domain, list_count)
- question: In light of the health and dietary changes discussed, what would be an appropriate gift for both Evan and Sam to encourage their healthy lifestyles?
- gold: 
- v98: The provided information is not enough to determine an appropriate gift.
- v101: A fitness tracker or a healthy recipe book would be an appropriate gift to encourage Evan and Sam's healthy lifestyles.

### Gain 8: 0063882ab0a923bfdb529626 (Single-Hop, fact_lookup)
- question: What event did John volunteer at last weekend?
- gold: 
- v98: community event to raise money for a good cause
- v101: career fair at a local school

### Gain 9: 0df391e1f684eeb22e522c4f (Single-Hop, fact_lookup)
- question: What is Melanie's hand-painted bowl a reminder of?
- gold: 
- v98: The provided information is not enough to determine what Melanie's hand-painted bowl is a reminder of, as Melanie does not own a hand-painted bowl in the context. Caroline is the one with a hand-painted bowl, which reminds her of art and self-expression.
- v101: art and self-expression

