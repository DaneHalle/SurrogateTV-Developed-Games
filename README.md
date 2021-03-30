# SurrogateTV-Developed-Games
Both game scripts I have developed for SurrogateTV. 

## SurroBros
SurroBros was launched on November 1st, 2020

Smash Bros Ultimate for the Switch was able to be played on the internet anywhere in the world by up to 4 players at a time. This was developed early in the surrortg-sdk development cycle when it was still in beta access. I was able to not only develop this but I was able to expand upon known ways to interface with the Switch through the SDK to allow up to 5 players at a time (settled for 4) off of a single Raspberry Pi 4 as opposed to the maximum at the time of 1 player per Pi. 

This game was taken offline for good on January 21st, 2021 due a user finding a way to get out of the game, into my Switch's settings, and factory reset it (resetting over 500 hours of game data and saves outside of Smash Bros). You can see the inactive game page at https://surrogate.tv/game/surrobros

### Reflection

SurroBros wasn't the best and most complex game but I will always be proud of it. Being that it was developed extremely early into the beta cycle of the surrortg-sdk, I had to figure a lot of stuff out on my own and develop new stuff to be later utilized within the SDK. The knowledge of being able to have up to 5 Trinket M0s running off of a single Raspberry Pi had not been previously done in my research for any purpose (SurrogateTV or otherwise). However, due to it being left fairly open and not restrictive like my later games, someone was able to get into my Switch's system settings and factory reset. To this day, I am still unsure of how they were able to crash into the home menu as there was no home button mapped through the site. The knowledge and experience gained from being an early adopter of the surrortg-sdk has allowed me to be a bank of knowledge in helping new users hook not only Switches but other things to Surrogate.tv. 

## BOTW
BOTW was launched on Feburary 5th, 2021

Zelda: Breath of the Wild for the Switch was able to be played on the internet anywhere in the world. Using the site's WePlay Model (Users get increments of time to compelte a game together), I made BOTW. Determined to not have the same outcome as SurroBros, I spent the between time setting up quite a number of IR trigger points to mitigate and stop users from getting to unintended menues and settings. Being that I was already developing a ton of IR triggers, I decided to make the game a more interactive experience, instead of the score on the site being "Games Played", I would have the game regocnize key points and items and hand out points. This would make it a competative, yet collaborative experience. 

This game is currently running and can be played at https://surrogate.tv/game/botw

### Reflection

The amount of time I put into developing this game in the way I did proved very effective in a modular way. The biggest issue plaguing it is reliance on custom made APIs which sometimes have IP changes on my local network, causing the game to become unplayable until I notice and fix it. Otherwise, everything has worked wonderfully and I have been able to utilize what I learned and developed to scale up and make a number of other games in a similar manner. 

## Super Mario Odyssey 
SMO was launched on March 19th, 2021 and is part of the RePlay game catalogue

Super Mario Odyssey for the Switch was able to be played on the internet anywhere in the world. Using the site's WePlay Model (Users get increments of time to compelte a game together), I made SMO. Extending what I learned from BOTW, I was able to easily get frames of data that could be used as IR trigger poitns to mitigate and stop users from getting to unintended menues and settings. 

This game is currently running and can be played at https://surrogate.tv/game/replay
