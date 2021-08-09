# o19 High Heels Auto Slider Mod
## Introduction

This mod allows to modify sliders based on the outfit. When a sim wears heels or boots the standard TS4 implementation reduces the length of the calf bone accordingly.
This mod can apply a scale slider to compensate this. The sim will be taller (or if desired for magical boots also smaller) in-game.

Also 'up/down' sliders are supported. The well-known 'SLIDER' boots usually use an 'up' (fly) slider. This works much better than scaling the whole sim.

## Warning

This is still an early access mod which adds sliders to your sim. Please make a backup of your save game and keep it for reference if you want to use this mod.
It takes about 0.5 seconds to set the sliders and the game may delay the adjustment of the settings even further.

Tested with 'The Sims 4' v1.77.131 (2021-07-23) and S4CL v1.71.
It may work with older and newer TS4 and S4CL versions.

## Installation
It is recommended to read the whole README.
To get started download the ZIP file and extract it to the 'The Sims 4' directory. 

Unless not yet installed: Install [S4CL](https://github.com/ColonolNutty/Sims4CommunityLibrary/releases/latest) as this mod is required.
I highly recommend to install both files to 'The Sims 4/Mods/_cn_/'.  

## Supported shoes

### Base game * EP * SP * AP
Currently many base game female shoes are supported.

Not supported:

+ EP09 Eco Lifestlye, EP10 Snowy Escape, EP11 Cottage Living, EP12+
+ GP09 Journey to Batuu, GP10 Dream Home, GP11+
+ SP12 Toddler Stuff
+ SP17 Nifty Knitting, SP18 Paranormal Stuff
+ SP19, SP24+
+ SP20 Throwback Fit Kit, SP21 Country Kitchen Kit, SP22 Bust the Dust Kit, SP23 Countryard Oasis Kit

### Dallasgirl79
Older shoes of [Dallasgirl79](https://dallasgirl79.tumblr.com/) are supported, but only the SLIDER version. The normal version is not supported.

The [Pia Heels](https://www.patreon.com/posts/39052976) heels are an exception as they do not support sliders. The setup is complicated with feet (CAS category: Shoes), random toe nail colors (CAS category: socks) and heels (CAS category: tights).

### Astya96
The Valentine slider Heels  of Astya96 https://www.patreon.com/posts/33961061 are supported.

### ATS4 (Deprecated)
The hoverboard https://sims4.aroundthesims3.com/objects/special_06.shtml is supported.
Support will be removed as de-spawning the hoverboard does not de-spawn properly.

## Supported walk styles
The walk style may be set based on the selected shoes or any other used CAS item.
The default walk style is 'Walk Feminine Slow'.

## Usage
The mod does not include a PIE menu interaction. It detects cloth changes and applies slider afterwards, based on the outfit (shoes).
It does not support all available shoes. Only shoes which are configured (see above) are supported.

## Customization
There is no option to gather slider values from a .package file. All configurations for CAS items is stored externally in the 'configuration' directory.

New sliders are configured there. Use 'TS MorphMaker 4.3.0.0 by CMAR' or something else to create new sliders is needed or use existing sliders.
Also the presets are stored there.

The _slider.sample.ini and _preset.sample.ini files contain more documentation.

Longer arms while wearing gloves, slim- or shapewear may also be configured. Also getting a long nose when wearing a special ring should work.
Both body and face sliders may be modified. Face presets can not be modified.

## Developers and Modders

Any help is welcome. I'm still looking for sliders to stretch the calf bone to use them instead of changing the scale of the sim.

The code is open source and is licenced as Attribution.

This version includes a lot of code to extract slider, walk style, CAS IDs and other game data which may be useful for other projects.
