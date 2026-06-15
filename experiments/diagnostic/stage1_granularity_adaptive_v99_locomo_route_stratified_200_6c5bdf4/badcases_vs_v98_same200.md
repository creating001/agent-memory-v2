# V99 Short Answer Boundary Diagnostic

- v98 same200: 165/200 = 0.825000
- v99 same200: 155/200 = 0.775000
- delta_vs_v98: -10
- prediction_changed_vs_v98: 95/200

## Losses

### 67f27e2361af6fb035a30c94
- route: fact_lookup
- question: Would Melanie be considered a member of the LGBTQ community?
- gold: Likely no, she does not refer to herself as part of it
- v98: No
- v99: The provided information is not enough.

### aa88e50253b91ab0fc834727
- route: fact_lookup
- question: What LGBTQ+ events has Caroline participated in?
- gold: Pride parade, school speech, support group
- v98: ['LGBTQ+ pride parade (3 July 2023)', 'LGBTQ conference (12 July 2023)', 'LGBTQ+ counseling workshop (27 June 2023)', 'school event (June 2023)', 'pride parade (14 August 2023)', 'LGBTQ art show (planned for August 2023)']
- v99: LGBTQ+ pride parade, LGBTQ conference, LGBTQ+ counseling workshop, mentorship program for LGBTQ youth, LGBTQ art show, LGBT pride event

### 09948051ad1179cead77946e
- route: fact_lookup
- question: Would Melanie go on another roadtrip soon?
- gold: Likely no; since this one went badly
- v98: No, Melanie would not go on another roadtrip soon.
- v99: The provided information is not enough.

### 65a58a5dd3bc5a5b7f9af9fe
- route: fact_lookup
- question: Would Caroline want to move back to her home country soon?
- gold: No; she's in the process of adopting children.
- v98: No, Caroline would not want to move back to her home country soon.
- v99: The provided information is not enough.

### 8db077bd9ef00b3cd8c4574e
- route: list_count
- question: What musical artists/bands has Melanie seen?
- gold: Summer Sounds, Matt Patterson
- v98: Matt Patterson, Summer Sounds, and an unnamed band
- v99: The provided information is not enough.

### 8c8a1e2cc1c2e9bc1a1dfc4a
- route: list_count
- question: What kind of professional experience did Gina get accepted for on May 23, 2023?
- gold: fashion internship
- v98: fashion internship
- v99: The provided information is not enough.

### b70696c900fd8410819acabc
- route: list_count
- question: What people has Maria met and helped while volunteering?
- gold: David, Jean, Cindy, Laura
- v98: Jean, Laura, a man, someone special
- v99: Jean, someone special, Laura

### a62c827bb1793e98e020b1f4
- route: list_count
- question: Around which US holiday did Maria get into a car accident?
- gold: Independence Day
- v98: Independence Day
- v99: The provided information is not enough.

### ddf916b77c5bce5ec5e24d3e
- route: profile_preference
- question: What is one of Joanna's favorite movies?
- gold: "Eternal Sunshineof the Spotless Mind"
- v98: romantic drama about memory and relationships
- v99: a romantic drama about memory and relationships

### c2502269932a17656749fc9d
- route: profile_preference
- question: What is Nate's favorite genre of movies?
- gold: Fantasy and sci-fi
- v98: action, fantasy, and sci-fi
- v99: action and sci-fi

## Gains

### d3a8d12b5be57abcc6ef6dc6
- route: list_count
- question: How many times has Melanie gone to the beach in 2023?
- gold: 2
- v98: 1
- v99: 2

### c0d93b5c24067d5dc35bf125
- route: list_count
- question: What European countries has Maria been to?
- gold: Spain, England
- v98: Spain
- v99: England, Spain
