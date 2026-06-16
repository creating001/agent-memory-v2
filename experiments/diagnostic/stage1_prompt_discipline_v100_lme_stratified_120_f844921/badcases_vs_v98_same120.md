# Badcases vs v98 on LME stratified 120

- v98 same120: 94/120 = 0.783333
- v100 same120: 89/120 = 0.741667
- delta_vs_v98: -5
- transitions: {'CORRECT->WRONG': 9, 'CORRECT->CORRECT': 85, 'WRONG->WRONG': 22, 'WRONG->CORRECT': 4}
- by_route: {'current_state': {'CORRECT->WRONG': 1, 'CORRECT->CORRECT': 2, 'WRONG->WRONG': 1}, 'fact_lookup': {'CORRECT->CORRECT': 43, 'WRONG->WRONG': 9, 'CORRECT->WRONG': 4, 'WRONG->CORRECT': 1}, 'list_count': {'CORRECT->CORRECT': 16, 'CORRECT->WRONG': 1, 'WRONG->CORRECT': 2, 'WRONG->WRONG': 2}, 'profile_preference': {'WRONG->WRONG': 5, 'WRONG->CORRECT': 1, 'CORRECT->CORRECT': 1}, 'temporal_lookup': {'CORRECT->CORRECT': 23, 'CORRECT->WRONG': 3, 'WRONG->WRONG': 5}}

## Losses: v98 CORRECT -> v100 WRONG

### Loss 1: 02e16bd2f4719927af0b2006 (knowledge-update, current_state)
- question: How many followers do I have on Instagram now?
- gold: 
- v98: 1300
- v100: 1250

### Loss 2: 2568a921ceb33f5c56f5647a (knowledge-update, fact_lookup)
- question: What was my previous personal best time for the charity 5K run?
- gold: 
- v98: 27 minutes and 45 seconds
- v100: 26 minutes and 30 seconds

### Loss 3: 59fa190fe4c30f70de47a73c (knowledge-update, list_count)
- question: How many different species of birds have I seen in my local park?
- gold: 
- v98: 32
- v100: 27

### Loss 4: 0e3b85f1ae5dddca4b328a0f (multi-session, temporal_lookup)
- question: How many fitness classes do I attend in a typical week?
- gold: 
- v98: 5
- v100: 4

### Loss 5: 1db38df3ec49cf8d8220ddc4 (multi-session, temporal_lookup)
- question: How many years older is my grandma than me?
- gold: 
- v98: 43
- v100: The provided information is not enough to answer the question: User's age is not provided, so the age difference cannot be calculated

### Loss 6: 25cafcb56c382cbde1cfcb13 (multi-session, temporal_lookup)
- question: How many weeks did it take me to watch all the Marvel Cinematic Universe movies and the main Star Wars films?
- gold: 
- v98: 3.5 weeks
- v100: The provided information is not enough to answer the question: No row provides the combined duration for both Marvel and Star Wars binges, nor confirms if they were consecutive or overlapping. Therefore, the total weeks cannot be calculated

### Loss 7: 27a28d49af7d327bb9f25309 (multi-session, fact_lookup)
- question: How much more did I spend on accommodations per night in Hawaii compared to Tokyo?
- gold: 
- v98: $270
- v100: The provided information is not enough to determine the exact difference in cost per night between accommodations in Hawaii and Tokyo.

### Loss 8: 5cd1177644ed9c8b6088d528 (single-session-assistant, fact_lookup)
- question: I'm checking our previous chat about the shift rotation sheet for GM social media agents. Can you remind me what was the rotation for Admon on a Sunday?
- gold: 
- v98: Admon was on the 8 am - 4 pm (Day Shift) on Sunday.
- v100: 8 am - 4 pm (Day Shift)

### Loss 9: 7f1ca033e152dbd9b1de7225 (single-session-preference, fact_lookup)
- question: I'm thinking of inviting my colleagues over for a small gathering. Any tips on what to bake?
- gold: 
- v98: Consider baking chewy chocolate chip cookies, healthier oatmeal raisin cookies with nuts, or a chocolate cake with caramel ganache frosting. A lemon lavender pound cake is also a great option for a unique flavor twist.
- v100: Consider making chewy chocolate chip cookies, oatmeal raisin cookies with nuts, or a lemon-lavender cake. These align with your past baking interests and preferences for flavorful, textured treats.

## Gains: v98 WRONG -> v100 CORRECT

### Gain 1: 128a1895ab851f148bbea790 (multi-session, list_count)
- question: How many plants did I initially plant for tomatoes and chili peppers?
- gold: 
- v98: The provided information is not enough to answer the question: initial plants for chili peppers
- v100: The provided information is not enough to answer the question: initial plants for chili peppers not mentioned in any memory

### Gain 2: 158692bc43ef28e0e43d991f (single-session-preference, profile_preference)
- question: Can you recommend some recent publications or conferences that I might find interesting?
- gold: 
- v98: The provided information is not enough to recommend specific recent publications or conferences.
- v100: Recent publications and conferences in deep learning for medical image analysis, particularly those focusing on explainable AI, multi-modal image fusion, transfer learning, domain adaptation, and model visualization, would be relevant. Consider journals like Medical Image Analysis or conferences such as MICCAI, CVPR, or NeurIPS tracks on medical imaging.

### Gain 3: 676f08cb0b1213adf24077d5 (single-session-preference, fact_lookup)
- question: I've been feeling nostalgic lately. Do you think it would be a good idea to attend my high school reunion?
- gold: 
- v98: Yes, attending your high school reunion could be a good idea, as you have positive memories from that time and have grown significantly since then.
- v100: Yes, attending your high school reunion could be a good idea, as you have positive memories of your time in high school, including being part of the debate team and taking AP economics courses.

### Gain 4: 0aa069360fca33f7e5eef027 (temporal-reasoning, list_count)
- question: How many charity events did I participate in before the 'Run for the Cure' event?
- gold: 
- v98: 3 charity events: Dance for a Cause, Food for Thought charity gala, Walk for Wildlife
- v100: 4 charity events: Dance for a Cause, Food for Thought, charity golf tournament, Walk for Wildlife

