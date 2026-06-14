# v80 delta badcases vs v79

只列出预测实际改变的 22 条；judge label 和 gold 只用于离线诊断，不能进入 prediction。

## 总览

- v79 accuracy: 0.784000
- v80 accuracy: 0.792000
- prediction_changed_count: 22
- changed net: 3 (WRONG->CORRECT 7 / CORRECT->WRONG 4)
- all-transition net: 4 correct
- update_conflict_guide_applied: 60

## 改对：WRONG -> CORRECT (7)

- `754c7fcd90f79025d3cf38eb` type=`multi-session` route=`fact_lookup`
  - Q: What is the total number of views on my most popular videos on YouTube and TikTok?
  - Gold: 1,998
  - v79: 2,000
  - v80: 1998
- `2a18e972b47c27c2c1f2fdb8` type=`temporal-reasoning` route=`current_state`
  - Q: How long have I been working before I started my current job at NovaTech?
  - Gold: 4 years and 9 months
  - v79: 4 years and 3 months
  - v80: 4 years and 9 months
- `96c4453d48cb9b5de348fd27` type=`knowledge-update` route=`fact_lookup`
  - Q: What was my personal best time in the charity 5K run?
  - Gold: 25 minutes and 50 seconds (or 25:50)
  - v79: 27:12
  - v80: 25:50
- `d40ed48e69924fa9eacc3216` type=`knowledge-update` route=`fact_lookup`
  - Q: What was the amount I was pre-approved for when I got my mortgage from Wells Fargo?
  - Gold: $400,000
  - v79: $350,000
  - v80: $400,000
- `2568a921ceb33f5c56f5647a` type=`knowledge-update` route=`fact_lookup`
  - Q: What was my previous personal best time for the charity 5K run?
  - Gold: 27 minutes and 45 seconds
  - v79: 26 minutes and 30 seconds
  - v80: 27 minutes and 45 seconds
- `af807a537c4950ead62c23aa` type=`knowledge-update` route=`current_state`
  - Q: How often do I play tennis with my friends at the local park previously? How often do I play now?
  - Gold: Previously, you play tennis with your friends at the local park every week (on Sunday). Currently, you play tennis every other week (on Sunday).
  - v79: Previously, I played tennis with my friends at the local park every other week. I still play with them at the local park every other week now.
  - v80: Previously, I played tennis with my friends at the local park weekly. Now, I play every other week.
- `02e16bd2f4719927af0b2006` type=`knowledge-update` route=`current_state`
  - Q: How many followers do I have on Instagram now?
  - Gold: 1300
  - v79: 1250
  - v80: 1300

## 未修复：WRONG -> WRONG (3)

- `32ebfa2049ba11bbc89d490c` type=`multi-session` route=`fact_lookup`
  - Q: How much will I save by taking the train from the airport to my hotel instead of a taxi?
  - Gold: $50
  - v79: 32
  - v80: 40
- `a3e4c89a8fdf800fa3b2676f` type=`temporal-reasoning` route=`current_state`
  - Q: What is the order of the three trips I took in the past three months, from earliest to latest?
  - Gold: I went on a day hike to Muir Woods National Monument with my family, then I went on a road trip with friends to Big Sur and Monterey, and finally I started my solo camping trip to Yosemite National Park.
  - v79: Sequoia National Park (2023-02-20), Muir Woods National Monument (2023-03-10), Big Sur and Monterey (2023-04-20)
  - v80: 1. Road trip to Yosemite National Park (2023-02-20), 2. Day hike to Muir Woods National Monument (2023-03-10), 3. Road trip to Big Sur and Monterey (2023-04-20)
- `f42847e71c4d486a8c6c7c0b` type=`temporal-reasoning` route=`current_state`
  - Q: What is the order of airlines I flew with from earliest to latest before today?
  - Gold: JetBlue, Delta, United, American Airlines
  - v79: American Airlines, Spirit Airlines, United Airlines, JetBlue, Delta
  - v80: American Airlines, United Airlines, Spirit Airlines, JetBlue, Delta

## 保持正确：CORRECT -> CORRECT (8)

- `6b71e7de361ac90841505bea` type=`multi-session` route=`fact_lookup`
  - Q: How much money did I raise for charity in total?
  - Gold: $3,750
  - v79: 3750
  - v80: $3,750
- `fda441172001a9a37348a9c9` type=`multi-session` route=`fact_lookup`
  - Q: What was the total number of people reached by my Facebook ad campaign and Instagram influencer collaboration?
  - Gold: 12,000
  - v79: 12000
  - v80: 12,000
- `5108082226f35be6c6705761` type=`multi-session` route=`fact_lookup`
  - Q: How much did I save on the designer handbag at TK Maxx?
  - Gold: $300
  - v79: $300
  - v80: 300
- `2dde93d290bf6754862f5ff1` type=`multi-session` route=`fact_lookup`
  - Q: What is the total time it takes I to get ready and commute to work?
  - Gold: an hour and a half
  - v79: 90 minutes
  - v80: 1 hour and 30 minutes
- `b4ec3f110dd096de84ccaf6e` type=`multi-session` route=`fact_lookup`
  - Q: How much did I save on the Jimmy Choo heels?
  - Gold: $300
  - v79: 300
  - v80: $300
- `1e069e9289cee627a448ce10` type=`temporal-reasoning` route=`fact_lookup`
  - Q: What was the first issue I had with my new car after its first service?
  - Gold: GPS system not functioning correctly
  - v79: The first issue was with the car's GPS system, which failed on March 22nd and was replaced by the dealership.
  - v80: GPS system issue
- `1f7723fca5c03dfc8ff0e0ca` type=`temporal-reasoning` route=`current_state`
  - Q: How long have I been working before I started my current job at Google?
  - Gold: The information provided is not enough. From the information provided, You haven't started working at Google yet.
  - v79: The provided information is not enough to determine how long the user has been working before starting at Google.
  - v80: The provided information is not enough to determine how long the user has been working before starting their current job at Google.
- `21fa5c20b675193587f70ed2` type=`knowledge-update` route=`fact_lookup`
  - Q: Before I purchased the gravel bike, do I have other bikes in addition to my mountain bike and my commuter bike?
  - Gold: Yes. (You have a road bike too.)
  - v79: Yes, before purchasing the gravel bike, you had a road bike in addition to your mountain bike and commuter bike.
  - v80: Yes, before purchasing the gravel bike, the user had a road bike in addition to the mountain bike and commuter bike.

## 回退：CORRECT -> WRONG (4)

- `ad7ea131cd126de5fca7057a` type=`multi-session` route=`fact_lookup`
  - Q: What is the total cost of Lola's vet visit and flea medication?
  - Gold: $75
  - v79: 75
  - v80: The total cost cannot be determined with the provided information because the vet visit cost is not specified in the current context.
- `7a09015c87580f2e98c3f5cd` type=`multi-session` route=`fact_lookup`
  - Q: What is the total number of comments on my recent Facebook Live session and my most popular YouTube video?
  - Gold: 33
  - v79: 12 comments on the recent Facebook Live session and 21 comments on the most popular YouTube video.
  - v80: 12 comments on the recent Facebook Live session and 21 comments on the most popular YouTube video
- `beb0a3bdb35a23a257132b5e` type=`knowledge-update` route=`current_state`
  - Q: Where did I go on my most recent family trip?
  - Gold: Paris
  - v79: Paris
  - v80: Hawaii
- `c8e1ba8228ec76a80757b503` type=`knowledge-update` route=`fact_lookup`
  - Q: What was my previous goal for my Apex Legends level before I updated my goal?
  - Gold: level 100
  - v79: level 100
  - v80: 100
