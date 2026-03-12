from __future__ import annotations

from pathlib import Path
from typing import Optional, Any, Tuple, List
import json
import random
import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPixmap, QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QMessageBox,
    QFileDialog,
    QLabel,
    QTabWidget,
    QComboBox,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QApplication,
    QGroupBox,
    QGridLayout,
    QScrollArea,
    QStackedWidget,
    QToolBar,
)

from app.config import CHARACTERS_DIR, DATA_DIR, project_root
from app.models import Character
from app.services import (
    list_character_files,
    load_character,
    save_character,
    delete_character_file,
)

from app.rules.weapons import WEAPONS_CATALOG, WEAPONS_BY_NAME
from app.rules.shields import SHIELD_CATALOG, SHIELD_BY_NAME
from app.rules.armor import ARMOR_CATALOG, ARMOR_BY_NAME

def build_arrow_icons_qss(icons_dir: str) -> str:
    """
    Returns QSS to force Qt arrow indicators to use our SVG icons.
    Works for QSpinBox/QDoubleSpinBox (QAbstractSpinBox) + QComboBox arrows.
    """
    d = Path(icons_dir)

    up            = (d / "turtle-arrow-up.svg").as_posix()
    up_hover      = (d / "turtle-arrow-up-hover.svg").as_posix()
    up_pressed    = (d / "turtle-arrow-up-pressed.svg").as_posix()

    down          = (d / "turtle-arrow-down.svg").as_posix()
    down_hover    = (d / "turtle-arrow-down-hover.svg").as_posix()
    down_pressed  = (d / "turtle-arrow-down-pressed.svg").as_posix()

    return f"""
/* ---------- SPINBOX UP/DOWN BUTTONS ---------- */
QAbstractSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 20px;
    border: none;
}}
QAbstractSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 20px;
    border: none;
}}

QAbstractSpinBox::up-arrow {{
    image: url("{up}");
    width: 14px;
    height: 14px;
}}
QAbstractSpinBox::up-arrow:hover {{
    image: url("{up_hover}");
}}
QAbstractSpinBox::up-arrow:pressed {{
    image: url("{up_pressed}");
}}

QAbstractSpinBox::down-arrow {{
    image: url("{down}");
    width: 14px;
    height: 14px;
}}
QAbstractSpinBox::down-arrow:hover {{
    image: url("{down_hover}");
}}
QAbstractSpinBox::down-arrow:pressed {{
    image: url("{down_pressed}");
}}

/* ---------- COMBOBOX DROPDOWN ARROW ---------- */
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
}}
QComboBox::down-arrow {{
    image: url("{down}");
    width: 14px;
    height: 14px;
}}
QComboBox::down-arrow:hover {{
    image: url("{down_hover}");
}}
QComboBox::down-arrow:on {{
    image: url("{down_pressed}");
}}
"""
APP_NAME = "TurtleCom"
APP_VERSION = "v2"

# ---------------- Dark theme (no arrow images here) ----------------
DARK_QSS = """
QWidget {
    background-color: #1e1e1e;
    color: #e6e6e6;
    font-size: 12pt;
}

QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QComboBox {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #3d6dcc;
}

QSpinBox, QDoubleSpinBox {
    background-color: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px;
    padding-right: 26px;
    selection-background-color: #3d6dcc;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    width: 22px;
    background: #2f2f2f;
    border-left: 1px solid #3a3a3a;
}

QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    border-bottom: 1px solid #3a3a3a;
    border-top-right-radius: 6px;
}

QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    border-bottom-right-radius: 6px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background: #3a3a3a;
}

QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
    background: #444444;
}

QTabWidget::pane {
    border: 1px solid #3a3a3a;
    border-radius: 8px;
}

QTabBar::tab {
    background: #2a2a2a;
    border: 1px solid #3a3a3a;
    padding: 8px 12px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

QTabBar::tab:selected {
    background: #333333;
    border-bottom-color: #333333;
}

QPushButton {
    background-color: #2f2f2f;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 8px 12px;
}

QPushButton:hover {
    background-color: #3a3a3a;
}

QPushButton:pressed {
    background-color: #444444;
}

QStatusBar {
    background-color: #1a1a1a;
    border-top: 1px solid #333333;
}

QMenuBar {
    background-color: #1e1e1e;
}

QMenuBar::item:selected {
    background-color: #333333;
}

QMenu {
    background-color: #1e1e1e;
    border: 1px solid #3a3a3a;
}

QMenu::item:selected {
    background-color: #333333;
}
"""


def _simple_attribute_mod(score: int) -> int:
    return max(0, (score - 10) // 2)


def _roll_d100() -> int:
    return random.randint(1, 100)


def _pick_from_ranges(table: list[tuple[range, str]], roll: int) -> str:
    for r, name in table:
        if roll in r:
            return name
    return ""


def _cost_to_int(cost: str) -> int:
    if not cost:
        return 0
    s = cost.strip().lower()
    if s in {"—", "-", "n/a"}:
        return 0
    if "not" in s and "sold" in s:
        return 0

    s = s.replace(",", "")
    s = s.replace(" ", "")
    s = s.replace("usd", "")
    s = s.replace("+", "")

    for sep in ("–", "-"):
        if sep in s and "$" in s:
            left = s.split(sep, 1)[0]
            return _cost_to_int(left)

    s = s.replace("$", "")

    mult = 1
    if s.endswith("k"):
        mult = 1000
        s = s[:-1]
    if s.endswith("mil"):
        mult = 1_000_000
        s = s[:-3]

    m = re.search(r"(\d+)", s)
    if not m:
        return 0
    return int(m.group(1)) * mult



# ---------------- Random Names by Animal ----------------
ANIMAL_NAME_POOLS: dict[str, list[str]] = {
    "POND TURTLE": [
        "Shellshock","Slice","Manhole","SewerJack","Puck","Brick","Graff","Neon","Drift","Ruckus",
        "Nori","Pepperoni","Tophat","Skidmark","Dojo","Scraps","Hinge","Wonton","Kickflip","Turnstile"
    ],
    "SNAPPING TURTLE": [
        "Chomp","Beartrap","Lockjaw","Cruncher","Vice","Clamp","Gatorade","Ripper","Ironbite","Snapperjack",
        "Gristle","Shredderbait","Scissorjaw","Knuckles","Bruiser","Gravel","Muzzle","Takedown","Boneclick","Jawline"
    ],
    "RAT": [
        "Splinter Jr.","Cheddar","Scurry","Alleycap","Squeakbox","KnickKnack","Grease","Nibbles","Whisk","Muzzle",
        "Rusty","Crumb","Domino","Metro","Patch","Tinfoil","Rook","Sneaker","Scamper","Trench"
    ],
    "RABBIT": [
        "Hopper","Thumper","Springheel","Flips","CarrotTop","Dash","Wiggler","Dandelion","Cotton","Kickster",
        "Binky","Speedbun","Snip","Tumble","Fuzzbyte","Moonhop","Flick","Quickstep","Pogo","Bunson"
    ],
    "RACCOON": [
        "Bandit","Mask","Dumpster Duke","Pickpocket","Snackrack","Nightcap","Grabbie","Scav","AlleyKing","Patchface",
        "Prowler","Lockpick","Scrabble","Gremlin","Slycan","Trash Panda","Swipe","Clatter","Pockets","Riggs"
    ],
    "FOX": [
        "Vixen","Redline","Slick","Ember","Whisper","Tailspin","Copper","Streetglow","Saffron","Quickmatch",
        "Mirage","Sidewind","Nighthush","Razorwink","Alleyfire","Torch","Hushpaw","Trickster","Cinder","Snapback"
    ],
    "WOLF": [
        "Howl","Greyson","Packrat","Nightbite","Frost","Timber","LunaTick","Streetfang","Rumble","Ironpaw",
        "Rookwolf","Midnight","Snarl","Tracker","Bricktooth","Shiver","Warg","Crosswalk","Clawson","Longstride"
    ],
    "DOG": [
        "Barker","Scruffy","K-9","Bolt","Fetch","Muttley","Chopper","Houndini","Bodega","Goodboy",
        "Collar","Rango","Paws","Juke","Spike","Bandana","Ruck","Tumbler","Biscuit","Bonehead"
    ],
    "CAT": [
        "Scratch","AlleyWhisk","Slink","Purrlock","Nightstitch","Clawdia","Velvet","Static","Razor","Tiptoe",
        "Flicker","Lynxie","Noodlecat","Sneer","Kite","Spindle","Hex","Mews","Glass","Shadowbox"
    ],
    "ALLIGATOR": [
        "Gator","Swampjack","Chisel","Bayou","Crocblock","Wrecker","Fangrail","Mudslide","Chompston","Toothrow",
        "Silt","Dockbite","Snapline","Riptide","Lockstep","Warth","SewerSaurus","Grin","Bucktooth","Brackish"
    ],
    "CROCODILE": [
        "Croc","Nile","Scutes","Razorsmile","Crankjaw","Bonegrip","Saltfang","Dreadsnout","Teethrow","Sawtooth",
        "RiverReaper","Scars","Gravelgrin","Breakwater","Snapcut","Knifemouth","Churn","Riptusk","Hardscale","Jawbrick"
    ],
    "BAT": [
        "Echo","Sonar","Nightwing","CaveFlip","Swoop","Fang","Velvetwing","Clicker","Gloom","Nocturne",
        "Hush","Wingtip","Radar","Blackout","Glider","Loophole","Skyrat","Umbra","Flutter","Darkstar"
    ],
    "BEAR": [
        "Bruin","Grumble","Tank","Kodiak","Smash","Granite","BigRig","Mauler","Honeybad","Snowplow",
        "Grizz","Barfight","Boulder","Tundra","Ironhug","Cinderpaw","Rumblebelly","Atlas","Freight","Growler"
    ],
    "SKUNK": [
        "Funk","Stinkbomb","Pepe","Spraypaint","Reek","Smog","Onion","Sulfur","Skid","Gaslight",
        "Boomcloud","Whiff","Nozzle","Mustard","Hazard","Skunkworks","Blackstripe","Stenchman","Reverb","Fumigator"
    ],
    "OTTER": [
        "Slip","Splash","Dockside","Ripple","Wave","Current","Whiskerfloat","Driftwood","Flipfin","Seaglass",
        "Buoy","Kelp","Clamslam","Surfside","Skimmer","Divebar","Foam","Waterline","Tides","Squeegee"
    ],
    "AARDVARK": [
        "Antsy","TongueTwister","Diggs","Termite","Snout","Burrow","Velcro","Slurp","Mound","Clawmark",
        "Dusty","Tunnelrat","Sticky","Shovel","Grubble","Rooter","Nightforage","Scoops","Sandman","Diggernaut"
    ],
    "FROG": [
        "Ribbit","Hopper","Slingshot","Tad","Croak","Skipper","Bogey","Swampflip","Lily","Springjack",
        "Gulp","Slick","Pondpunk","Bullfrog","Flycatch","Greenbean","Mudskip","Bounce","Wartlock","Plop"
    ],
    "TOAD": [
        "Wart","Grumble","Toxin","Bump","Bogart","Sludge","Croaker","Toadstool","Puddle","Grub",
        "Hopsmack","Splat","Mire","Blister","Squelch","Mossback","Swamper","Slop","Grit","Lump"
    ],
    "SALAMANDER": [
        "Ember","Ash","Cinder","Regen","Slickskin","Newtrock","Glowtail","Blaze","Scorch","Kindler",
        "Flare","Torchlet","Smolder","Sparkplug","Heatwave","Flashpoint","Salamax","Burnout","Flicker","Ignite"
    ],
    "NEWT": [
        "Ripple","Skitter","Damp","Moss","Skim","Lurk","Reed","Glimmer","Dewdrop","Murk",
        "Brook","Flick","Skulk","Peat","Shimmer","Drift","Mist","Gully","Shade","Wisp"
    ],
    "AXOLOTL": [
        "Axel","Lottie","Gills","Frillz","RegenX","Pinky","Tank","Noodle","Bubble","Twitch",
        "Hydro","Smiley","Squish","Ripplegill","Glowup","Splashy","Wiggle","Mudbud","Flow","Salamigo"
    ],
    "CHIMPANZEE": [
        "Knuckle","Zip","Barrel","Scrap","Ruck","Smirk","Clutch","Brawl","Twitch","Bronx",
        "Grip","Skirmish","Hustle","Jive","Tag","Quickhands","Sidekick","Snap","Piston","Rumble"
    ],
    "GORILLA": [
        "Knox","Atlas","Tank","Thunder","Brick","Ironback","Titan","Slam","Boulder","Forge",
        "Crush","Granite","Biggs","Stomp","Colossus","Raze","Mammoth","Havoc","Goliath","Wrecka"
    ],
    "ORANGUTAN": [
        "Rust","Borneo","Longarm","Tango","Emberfur","Branch","Redwood","Saffron","Swing","Canopy",
        "Treetop","Driftwood","Clasp","Marrow","Tangle","Vine","Copper","Latch","Grove","Knots"
    ],
    "ARMADILLO": [
        "Roller","Armor","Shellshock","Plates","Tankette","Hardcase","Bolt","Crashbar","Ironhide","Rumbleball",
        "Knuckledome","Spindle","Rivet","Shield","Buckler","Curbside","Slamroll","Ironclad","Rollo","Barricade"
    ],
    "BADGER": [
        "Snarl","Diggory","Fury","Stripe","Maul","Scrapper","Gnash","Bristle","Dirtclaw","Grudge",
        "Fangface","Brawler","Clutch","Hardscrabble","Spite","Tunnel","Spade","Ruckus","Slash","Biteback"
    ],
    "BEAVER": [
        "Timber","Chisel","Dammer","Plank","Rivet","Paddle","Sawdust","Logjam","Cedar","Whittle",
        "Bracket","Dock","Mason","Gnawson","Lumber","Trestle","Notch","Beam","Spillway","Timberjack"
    ],
    "BUFFALO": [
        "Stampede","Hornet","Prairie","Dustcloud","Humpback","Bramble","Ironhorn","Driftplain","Snort","Trample",
        "Thunderhoof","Bisonic","Shag","Plainsman","Rumblehorn","Hoofprint","Brawlback","Flint","Boulderhorn","Tundra"
    ],
    "BISON": [
        "Gravelmane","Ironbuff","Plainsrage","Stamp","Dusthorn","PrairieKing","Hoofslam","Roughneck","Wildmane","Backtrail",
        "Rumblehide","Frontier","Tusk","Brutehoof","Oxide","Plainslash","Driftmane","Snag","Bramblehorn","Brawlplain"
    ],
    "CAMEL": [
        "Humpday","Dune","Spitfire","Mirage","Sandstorm","Caravan","Sirocco","Nomad","Sahara","Oasis",
        "Tumbleweed","Longstride","Dustwalker","Cactus","Sunburn","Drydock","Bristle","Scorchstep","Trailblaze","Silt"
    ],
    "ELEPHANT": [
        "Trunkline","Stamp","Ivory","BigRig","Mammoth","Tusk","Thunderstep","Wrinkle","Atlas","Stampede",
        "Tanker","Rumbletrunk","Colossus","Pachy","Ironhide","Longnose","Howdah","Boomfoot","Gravelstep","Temple"
    ],
    "BOBCAT": [
        "Bobwire","Scruff","Shorttail","Slash","Alleyclaw","Spindle","Hissfit","Razorback","Prowl","Tangle",
        "Fangline","Whisk","Snapclaw","Thorn","Rook","Sideburn","Lynk","Slink","Patchfur","Skirmish"
    ],
    "LYNX": [
        "Tuft","Frostbite","Snowclaw","Icewhisk","Glare","Longstep","Northpaw","Shiver","Hushclaw","Driftfang",
        "Paleeye","Timberline","Ghostfur","Rime","Slashmark","Coldshot","Flurry","Talonette","Ridge","Silentstep"
    ],
    "CHEETAH": [
        "Blitz","Zipline","Overdrive","Dash","Nitro","Quickstrike","Skid","Warp","Velocity","Streak",
        "Soniclaw","Burnout","Fastlane","Flashpaw","Rapid","Slipstream","Hotfoot","Rush","Zinger","Breakneck"
    ],
    "COUGAR": [
        "Puma","Ridge","Longfang","Shadowstep","Highclaw","Cliff","Striker","Nightprowl","Dustfang","Canyon",
        "Roamer","Backtrail","Leanpaw","Rumblecat","Fangline","Quickclaw","Mesa","Snapstep","Sundown","Tracker"
    ],
    "JAGUAR": [
        "Onyx","Spotlock","Jungle","Crushfang","Nightroar","Goldclaw","Prowler","Fangstorm","Rainclaw","Shadowspot",
        "Razorhide","Sunjag","Driftclaw","Roarline","Coil","Strangle","Stealthbite","Templefang","Darkmark","Viperclaw"
    ],
    "LEOPARD": [
        "Spots","Ghostspot","Treeclaw","Nightcoil","Whiptail","Fade","Dapple","Stealthpaw","Fangdash","Rooftop",
        "Hushfang","Branchline","Quickspot","Alleyprowl","Snapfang","Glint","Silkclaw","Emberpaw","Swiftbite","Shadewalker"
    ],
    "LION": [
        "Mane","Roar","Crown","Pride","Kingpin","Goldmane","Rumbleking","Sunfang","Brickmane","Rex",
        "Roarshock","Clutchmane","Savanna","Torchmane","Rampart","Fanglord","Brass","Roarlock","Monarch","Grandleap"
    ],
    "TIGER": [
        "Stripe","Shred","Ironstripe","Clawstorm","Bengal","Blazeclaw","Nightstripe","Snarlburn","Razorstripe","Emberfang",
        "Warstripe","Crushclaw","Thunderstripe","Wildmark","Snapstripe","Fangrush","Burnstripe","Grimstripe","Slashfang","Apex"
    ],
    "GOAT": [
        "Headbutt","Hornlock","Billy","Ramjam","Hoofbeat","Cliffkick","Scramble","Nanny","Ironhorn","Butthead",
        "Ridgekick","Springhorn","Tanglebeard","Rockhop","Crag","Bash","Knucklegoat","Pebble","Hornswoggle","Mountain"
    ],
    "HIPPOPOTAMUS": [
        "Hipshot","Mudjaw","Riverbrick","BigChomp","Gully","Tankmouth","Floodgate","Slamjaw","Wallow","Swampthud",
        "Brickhide","Rumblejaw","Marsh","Breakwater","Siltstep","Grincrusher","Bogbuster","Hydrothud","Snapmud","Undertow"
    ],
    "HORSE": [
        "Gallop","Stirrup","Mustang","Longstride","Hoofbeat","Bridle","ManeEvent","Colt","Trotter","Spur",
        "Stamp","Haymaker","Trackstar","Bronco","Whinny","Reins","Buckshot","Ironhoof","Derby","Windrunner"
    ],
    "LEMUR": [
        "Ringtail","Zing","Treehop","Flicktail","Maskette","Vineflip","Madagascar","Skitter","Cling","Bounceback",
        "Longlook","Slinktail","Jester","Prism","Snaggle","Rooftree","Hopscotch","Treetrick","Sideglance","Snapvine"
    ],
    "GECKO": [
        "Stickshift","Velcro","Wallride","Skitter","Grip","Crawlspace","Neonhide","Quickpad","Scalewire","Flicktail",
        "Sideclimb","Flashscale","Limebite","Snaptoe","Rafter","Rooftile","Zipwall","Cling","Driftcrawl","Nightpad"
    ],
    "SKINK": [
        "Slipscale","Gloss","Smooth","Skitterline","Scaleback","Flashhide","Copperflash","Slitherstep","Quicktail","Sunskink",
        "Flicker","Gleam","Dashscale","Hardsheen","Skim","Slidebite","Ridgeflash","Snapscale","Slinker","Burnscale"
    ],
    "CHAMELEON": [
        "Shift","Fadeout","Prism","Blend","Ghost","Hue","Mirage","Spectrum","Patch","Vanish",
        "Chromo","Backdrop","Tint","Ripplehide","Colorlock","Maskfade","Paintjob","Sneakshade","Dazzle","Kaleido"
    ],
    "GILA MONSTER": [
        "Venom","Beadbite","Toxiclaw","Heatrock","Scorchscale","Slowburn","Spinebite","Poisonjaw","Desertfang","Emberhide",
        "Coilbite","Fangsnap","Rustscale","Biteforce","Viperjaw","Heatclaw","Toxin","Burnfang","Shockbite","Cinderclaw"
    ],
    "IGUANA": [
        "Iggy","Spiketail","Sunscale","Leafbite","Crest","Thornback","Tropiclaw","Vineclimb","Heatwave","Junglejack",
        "Scalewhip","Frill","Rooftopscale","Dayglo","Latch","Thornstripe","Palmclaw","Canopy","Sizzle","Rainclimb"
    ],
    "KOMODO DRAGON": [
        "Komodo","Doomodo","Dragonjaw","Warfang","Venomking","Apexscale","Ironfang","Slaughtertail","Bloodbite","Crushscale",
        "Doomclaw","Titanlizard","Maw","Bonefang","Reaperhide","Gritjaw","Skullscale","Deathcoil","Rumblefang","Overlord"
    ],
    "MARTEN": [
        "Pineclaw","Quickfur","Timberdash","Sleek","Branchbite","Slinker","Frostfur","Treetrick","Snapvine","Ridgetail",
        "Swiftpelt","Fangtwig","Hushfur","Clamber","Sprig","Darkpine","Skirmish","Needle","Tanglefur","Volebane"
    ],
    "MINK": [
        "Velvet","Slickfur","Riverfang","Gloss","Wetnose","Shadowfur","Glidepaw","Driftfang","Ink","Streamline",
        "Ripplefang","Blackwater","Softbite","Sheen","Dockclaw","Quickpelt","Slinkwave","Nightfur","Daggerfur","Undertow"
    ],
    "MOLE": [
        "Diggler","Blindside","Dirtnap","Burrow","Shovel","Tunnelrat","Earthmover","Snout","Grub","Subterra",
        "Mudslide","Gravelnose","Deepcore","Driftsoil","Trench","Nightburrow","Quake","Grit","Hollow","Undermine"
    ],
    "MONKEY": [
        "Branch","Zipvine","Swing","Bananas","Clutch","Treejack","Quickgrip","Rooftop","Jinx","Snapvine",
        "Dashbranch","Treetop","Skitter","Barrel","Vineshock","Highwire","Clamber","Riff","Junglejuke","Hopscotch"
    ],
    "BABOON": [
        "Redfang","Bruiser","Snarlface","Mandrill","Stonejaw","Packlord","Knuckle","Ruckus","Grizzle","Brawlmark",
        "Fanglash","Dustsnout","Warcry","Backhand","Ironcheek","Tuskjaw","Tribe","Roarback","Skullbash","Rumbleface"
    ],
    "MUSKRAT": [
        "Paddle","Reed","Driftwood","Gnaw","Mudbank","Damjack","Ripple","Whisker","Brook","Chewtoy",
        "Dockrat","Swampy","Float","Skim","Marshbite","Puddle","Nibblet","Bankshot","Slicktail","Waterlog"
    ],
    "PIG": [
        "Porkchop","Snout","Trotter","Mudpie","Oinker","Brickbelly","Gristle","Hogwash","Hamfist","Sty",
        "Rooter","Lard","Boink","Tusklet","Swill","Bellyslam","Grunt","Chopstick","Hambo","Slop"
    ],
    "BOAR": [
        "Razorback","Tusk","Gore","Ironhog","Wildfang","Bristleback","Slashsnout","Mudfang","Warhog","Spinehide",
        "Rumbletusk","Fangrush","Bloodsnout","Trample","Rootlash","Spiketail","Brawler","Hardtusk","Ravage","Thornhog"
    ],
    "PORCUPINE": [
        "Quill","Pinprick","Spines","Needles","Barbwire","Spikeball","Thorn","Stickup","Hedge","Pointblank",
        "Cactus","Spineclash","Prickles","Dartback","Burr","Shard","Spiker","Quillshock","Splinterpoint","Hedgehog"
    ],
    "OPOSSUM": [
        "Roadkill","Grim","Hiss","Ghosttail","Deadpan","Playdead","Switch","Paleclaw","Nightdrop","Alleyghost",
        "Possum","Shade","Drool","Faux","Backtrack","Hangtail","Undertaker","Twitch","Skulk","Whitefang"
    ],
    "SHARK": [
        "Fin","Chum","Biteforce","Riptide","Bloodwake","Deepjaw","Hammer","Reef","Undertow","Jaws",
        "Brine","Surge","Trawler","Coldfin","Tidemark","Breakwater","Slashfin","Abyss","Mako","Gnasher"
    ],
    "SHEEP": [
        "Wooly","Ramble","Headbutt","Fleece","Lambchop","Cotton","Bleat","Fluff","Hornet","Shear",
        "Hoofball","Pasture","Mutton","Snowcoat","Baa-dude","Cloud","Woolshock","Ramrod","Ewe-turn","Haystack"
    ],
    "SQUIRREL": [
        "Nutjob","Acorn","Ziptail","Treebolt","Skitter","Bushytail","Scurry","Rooftop","Twitch","Parkour",
        "Nibble","Whiptail","Branchdash","Chatter","Quicknut","Sideclimb","Gnawjack","Flip","Wiretail","Speednut"
    ],
    "WEASEL": [
        "Sneak","Sliver","Fanglet","Quickfang","Slipknife","Razorfur","Coil","Twitchfang","Slink","Fangdash",
        "Slim","Dagger","Shank","Fangwink","Leanbite","Needlefang","Whiplash","Quickslash","Narrow","Viperfur"
    ],
    "FERRET": [
        "Bandit","Wiggle","Scruff","Noodle","Quickburrow","Dashfur","Mask","Twitch","Scamper","Longshot",
        "Fuzz","Snapfur","Rocket","Slalom","Whisk","Zinger","Tunnelzip","Mischief","Fidget","Skid"
    ],
    "WOLVERINE": [
        "Fury","Ironclaw","Maul","Raze","Frostfang","Snarl","Breakclaw","Warfang","Havoc","Ridgeclaw",
        "Fangstorm","Brawlhide","Savage","Grimclaw","Ripper","Crushfang","Doomclaw","Nightmaul","Backbreaker","Rampage"
    ],
    "MOUSE": [
        "Squeak","Pip","Nibbler","Tiny","Scamper","Crumb","Whisk","Cheddar","Skitter","Peep",
        "Button","Dash","Snip","Flick","Trickle","Slink","Pebble","Rattle","Tippy","Whisp"
    ],
    "GERBIL": [
        "Zippy","Sanddash","Pebbles","Whirl","Dune","Twitcher","Scamperjack","Burrowbug","Flip","Skip",
        "Sunpaw","Nibblet","Zoomer","Sprint","Fidget","Skidder","Hopper","Dusty","Rustle","Quicktail"
    ],
    "HAMSTER": [
        "Roller","Cheeks","Wheelie","Nugget","Fuzzball","Spin","Chompette","Biscuit","Tubby","Dashball",
        "Puff","Snacker","Peanut","Turbo","Crumbler","Hopperton","Snackjack","Whiskers","Rollout","Squeaker"
    ],
    "GUINEA PIG": [
        "Gizmo","Squealer","Pudge","Fuzz","Pebble","Pipsqueak","Chatter","Sniff","Whistle","Cabbage",
        "Buttonnose","Tater","Rumblecheek","Nibblebug","Fritter","Puffball","Patch","Nuzzle","Toot","Scooter"
    ],
    "PIKA": [
        "Peak","Yodel","Cliffdash","Frosthop","Alpine","Scree","Pebblesnap","Rockhopper","Summit","Skitterpeak",
        "Whistlejaw","Crag","Snowblink","Ridgehop","Boulderbit","Highnote","Mountainzip","Chillhop","Quickpeak","Stonewhisk"
    ],
}


# ---------------- Vehicles (from scan) ----------------
VEHICLES_LANDCRAFT: list[dict[str, str]] = [
    {"name": "Skateboard/Scooter", "range": "—", "top_speed": "15 mph", "sdc": "25", "cost": "$250"},
    {"name": "Bicycle", "range": "—", "top_speed": "25 mph", "sdc": "60", "cost": "$500"},
    {"name": "Dirt Motorbike", "range": "100 miles", "top_speed": "75 mph", "sdc": "100", "cost": "$2k"},
    {"name": "Street Motorcycle", "range": "200 miles", "top_speed": "100 mph", "sdc": "125", "cost": "$5k"},
    {"name": "Speed Motorcycle", "range": "150 miles", "top_speed": "150 mph", "sdc": "100", "cost": "$10k"},
    {"name": "Cruiser Motorcycle", "range": "250 miles", "top_speed": "125 mph", "sdc": "150", "cost": "$15k"},
    {"name": "Compact Car", "range": "350 miles", "top_speed": "100 mph", "sdc": "250", "cost": "$20k"},
    {"name": "Sedan", "range": "300 miles", "top_speed": "120 mph", "sdc": "350", "cost": "$25k"},
    {"name": "Luxury Sedan", "range": "300 miles", "top_speed": "120 mph", "sdc": "375", "cost": "$50k+"},
    {"name": "Sports Car", "range": "250 miles", "top_speed": "150 mph", "sdc": "300", "cost": "$50k+"},
    {"name": "Mini-Van", "range": "350 miles", "top_speed": "100 mph", "sdc": "350", "cost": "$30k"},
    {"name": "Full-Sized Van", "range": "200 miles", "top_speed": "120 mph", "sdc": "375", "cost": "$30k"},
    {"name": "Sport Utility Vehicle", "range": "200 miles", "top_speed": "120 mph", "sdc": "400", "cost": "$35k"},
    {"name": "Truck (4WD)", "range": "200 miles", "top_speed": "120 mph", "sdc": "425", "cost": "$30k"},
    {"name": "Moving Truck", "range": "500 miles", "top_speed": "75 mph", "sdc": "375", "cost": "$40k"},
    {"name": "Semi-Truck", "range": "400 miles", "top_speed": "100 mph", "sdc": "600", "cost": "$100k"},
]

VEHICLES_WATERCRAFT: list[dict[str, str]] = [
    {"name": "*Surfboard", "range": "—", "top_speed": "15 mph", "sdc": "30", "cost": "$500"},
    {"name": "Canoe/Kayak", "range": "—", "top_speed": "10 mph", "sdc": "60", "cost": "$1k"},
    {"name": "Rowboat", "range": "—", "top_speed": "10 mph", "sdc": "100", "cost": "$1.5k"},
    {"name": "*Sailboat, Small", "range": "—", "top_speed": "15 mph", "sdc": "150", "cost": "$10k"},
    {"name": "*Sailboat, Medium", "range": "—", "top_speed": "20 mph", "sdc": "300", "cost": "$25k"},
    {"name": "Jet Ski", "range": "50 miles", "top_speed": "40 mph", "sdc": "75", "cost": "$5k"},
    {"name": "Fanboat", "range": "100 miles", "top_speed": "50 mph", "sdc": "250", "cost": "$10k"},
    {"name": "Motorboat, Small", "range": "100 miles", "top_speed": "30 mph", "sdc": "175", "cost": "$12k"},
    {"name": "Motorboat, Medium", "range": "500 miles", "top_speed": "40 mph", "sdc": "350", "cost": "$30k"},
    {"name": "Speedboat", "range": "50 miles", "top_speed": "80 mph", "sdc": "250", "cost": "$40k"},
    {"name": "Yacht, Medium", "range": "500 miles", "top_speed": "40 mph", "sdc": "375", "cost": "$100k"},
    {"name": "Yacht, Large", "range": "1k miles", "top_speed": "40 mph", "sdc": "500", "cost": "$500k"},
]

VEHICLES_AIRCRAFT: list[dict[str, str]] = [
    {"name": "*Hot Air Balloon", "range": "25 miles", "top_speed": "10 mph", "sdc": "50", "cost": "$20k"},
    {"name": "*Hang Glider", "range": "50 miles", "top_speed": "40 mph", "sdc": "50", "cost": "$5k"},
    {"name": "*Glider", "range": "250 miles", "top_speed": "75 mph", "sdc": "150", "cost": "$25k"},
    {"name": "Jet Pack", "range": "25 miles", "top_speed": "100 mph", "sdc": "75", "cost": "$100k"},
    {"name": "Ultralight", "range": "250 miles", "top_speed": "75 mph", "sdc": "100", "cost": "$10k"},
    {"name": "Biplane, 2-seater", "range": "400 miles", "top_speed": "150 mph", "sdc": "250", "cost": "$50k"},
    {"name": "Private Plane, Small", "range": "600 miles", "top_speed": "150 mph", "sdc": "300", "cost": "$100k"},
    {"name": "Helicopter, Small", "range": "500 miles", "top_speed": "200 mph", "sdc": "250", "cost": "$750k"},
    {"name": "Helicopter, Medium", "range": "500 miles", "top_speed": "200 mph", "sdc": "400", "cost": "$2mil"},
    {"name": "Bush Plane, 4-seater", "range": "700 miles", "top_speed": "175 mph", "sdc": "350", "cost": "$500k"},
    {"name": "Bush Plane, 10-seater", "range": "1000 miles", "top_speed": "200 mph", "sdc": "600", "cost": "$2mil"},
    {"name": "Private Jet", "range": "1500 miles", "top_speed": "500 mph", "sdc": "750", "cost": "$5mil"},
]

VEHICLES_LOOKUP: dict[str, dict[str, str]] = {
    v["name"]: v for v in (VEHICLES_LANDCRAFT + VEHICLES_WATERCRAFT + VEHICLES_AIRCRAFT)
}

# ---------------- Equipment catalogs ----------------

GEAR_CATALOG: list[dict[str, Any]] = [
    {"name": "Handgun Ammo (50 rds) - Low/Med (.22/.32/.38/9mm)", "cost": "$15", "details": "Ammo"},
    {"name": "Handgun Ammo (50 rds) - Heavy (.38+P/.357/.45)", "cost": "$30", "details": "Ammo"},
    {"name": "Rifle/Shotgun Ammo (20 rds) - Low/Med (.223/5.56/7.62)", "cost": "$10", "details": "Ammo"},
    {"name": "Rifle/Shotgun Ammo (20 rds) - Heavy (.308/12-gauge)", "cost": "$20", "details": "Ammo"},
    {"name": "Tie Tack Mic", "cost": "$150", "details": "Bugs (Hidden Mics)"},
    {"name": "Contact Mic", "cost": "$300", "details": "Bugs (Hidden Mics)"},
    {"name": "Keyhole/Tube Mic", "cost": "$300", "details": "Bugs (Hidden Mics)"},
    {"name": "Room Bugs", "cost": "$150–$500", "details": "Bugs (Hidden Mics)"},
    {"name": "Specialized Micro Bugs", "cost": "$200–$1000", "details": "Bugs (Hidden Mics)"},
    {"name": "GPS Tracker", "cost": "$100", "details": "Tracking Devices"},
    {"name": "Acoustic Noise Generator", "cost": "$900", "details": "Bug Detectors"},
    {"name": "Broadband Detector", "cost": "$500", "details": "Bug Detectors"},
    {"name": "Radio Detector", "cost": "$400", "details": "Bug Detectors"},
    {"name": "Binoculars (300 yd)", "cost": "$250", "details": "Optics"},
    {"name": "Binoculars (1500 yd)", "cost": "$500", "details": "Optics"},
    {"name": "Binoculars (3000 yd)", "cost": "$1000", "details": "Optics"},
    {"name": "Weapon Scope", "cost": "$250–$2000", "details": "Optics"},
    {"name": "Nightvision Goggles (100 yd)", "cost": "$10,000", "details": "Optics"},
    {"name": "Nightvision Binoculars (100 yd)", "cost": "$10,000", "details": "Optics"},
    {"name": "Nightvision Monocular (100 yd)", "cost": "$1500", "details": "Optics"},
    {"name": "Nightvision Weapon Sight (100 yd)", "cost": "$2000", "details": "Optics"},
    {"name": "Nightvision Tripod Mount", "cost": "$2000", "details": "Optics"},
    {"name": "Thermal Imaging Goggles (2000 yd)", "cost": "$30,000", "details": "Optics"},
    {"name": "Thermal Imaging Binoculars (2000 yd)", "cost": "$30,000", "details": "Optics"},
    {"name": "Thermal Imaging Monocular (2000 yd)", "cost": "$28,000", "details": "Optics"},
    {"name": "Thermal Imaging Weapon Sight (2000 yd)", "cost": "$20,000", "details": "Optics"},
    {"name": "Explosives Detector", "cost": "$2000", "details": "Detection Equipment"},
    {"name": "Letter Bomb Detector", "cost": "$1000", "details": "Detection Equipment"},
    {"name": "Radar Signal Detector", "cost": "$1000", "details": "Detection Equipment"},
    {"name": "Motion Detector", "cost": "$250", "details": "Detection Equipment"},
    {"name": "Microwave Fence System", "cost": "$50,000", "details": "Detection Equipment"},
    {"name": "Digital Camera", "cost": "$250", "details": "Recording"},
    {"name": "DSLR", "cost": "$750", "details": "Recording"},
    {"name": "Lavalier Mic", "cost": "$500", "details": "Recording"},
    {"name": "Handheld Mic", "cost": "$500", "details": "Recording"},
    {"name": "Video Camera", "cost": "$750", "details": "Recording"},
    {"name": "Tablet", "cost": "$1000", "details": "Computers"},
    {"name": "Laptop", "cost": "$1500", "details": "Computers"},
    {"name": "Desktop", "cost": "$2000", "details": "Computers"},
    {"name": "Pro Desktop", "cost": "$2500", "details": "Computers"},
    {"name": "Mobile Phone", "cost": "$250", "details": "Communications"},
    {"name": "Smartphone", "cost": "$1000", "details": "Communications"},
    {"name": "Walkie-Talkie (5 mi)", "cost": "$250", "details": "Communications"},
    {"name": "Walkie-Talkie (10 mi)", "cost": "$500", "details": "Communications"},
    {"name": "CB Radio (5 mi)", "cost": "$1000", "details": "Communications"},
    {"name": "Police Scanner (10 mi)", "cost": "$2000", "details": "Communications"},
    {"name": "Field Radio (50 mi / global satellite)", "cost": "$5000", "details": "Communications"},
    {"name": "Radio Jammer (handheld)", "cost": "$500", "details": "Communications"},
    {"name": "Radio Jammer (backpack)", "cost": "$25,000", "details": "Communications"},
    {"name": "Radio Jammer (large)", "cost": "$75,000", "details": "Communications"},
    {"name": "Armored Attaché Case (AR 15, SDC 100)", "cost": "$500", "details": "Adventuring"},
    {"name": "Pepper Spray", "cost": "$50", "details": "Adventuring"},
    {"name": "Tear Gas Spray", "cost": "$25", "details": "Adventuring"},
    {"name": "Electro-Adhesive Pads", "cost": "$1500", "details": "Adventuring"},
    {"name": "Heavy Duty Flashlight (1D6)", "cost": "$200", "details": "Adventuring"},
    {"name": "Handcuffs (Novelty)", "cost": "$50", "details": "Adventuring"},
    {"name": "Handcuffs (Law Enforcement)", "cost": "$100", "details": "Adventuring"},
    {"name": "Illuminating Penlight", "cost": "$100", "details": "Adventuring"},
    {"name": "Nightstick (1D6+1)", "cost": "$50", "details": "Adventuring"},
    {"name": "Sap Gloves (+2 damage)", "cost": "$50", "details": "Adventuring"},
    {"name": "Space Suit (US)", "cost": "$500,000", "details": "Adventuring"},
    {"name": "Space Suit (Russian)", "cost": "$50,000", "details": "Adventuring"},
    {"name": "Stun Gun", "cost": "$100", "details": "Adventuring"},
    {"name": "Taser", "cost": "$1000", "details": "Adventuring"},
    {"name": "First Aid Pouch", "cost": "$100", "details": "Adventuring"},
    {"name": "Multitool", "cost": "$100", "details": "Adventuring"},
    {"name": "Lock Pick Set", "cost": "$100", "details": "Adventuring"},
    {"name": "Lock Pick Gun", "cost": "$3000", "details": "Adventuring"},
    {"name": "Repair Kit", "cost": "$250", "details": "Adventuring"},
    {"name": "Medical Kit", "cost": "$500", "details": "Adventuring"},
]

# ===================== ADD THESE NEW CONSTANTS + LOOKUPS (place near your other catalogs/constants) =====================

HUMAN_FEATURE_OPTIONS: list[tuple[str, int]] = [
    ("None (0 Bio-E)", 0),
    ("Partial (5 Bio-E)", 5),
    ("Full (10 Bio-E)", 10),
]

# Psionics: you said "general" and "limit to 5 available" for now.
# Costs were not specified; using a simple placeholder (10 Bio-E each). Adjust freely.
PSIONIC_POWER_OPTIONS: list[tuple[str, int]] = [
    ("None (0 Bio-E)", 0),
    ("Mind Block (10 Bio-E)", 10),
    ("Telepathy (10 Bio-E)", 10),
    ("Object Read (10 Bio-E)", 10),
    ("Sixth Sense (10 Bio-E)", 10),
    ("Empathy (10 Bio-E)", 10),
]

# Bio-E animal data (PLACEHOLDERS). Expand this table as you add real animal rules.
# - bio_e: starting points granted when animal is selected
# - original: original animal characteristics to display
# - mutant_changes_text: freeform text shown in "Mutant changes & Costs"
# - natural_weapons: up to 5 options (name, cost, details)
# - abilities: up to 10 options (name, cost, details)
# - attribute_bonuses: optional dict shown in Attribute Bonuses display

BIOE_ANIMAL_DATA: dict[str, dict[str, Any]] = {

# (i.e., between the opening { and closing } of that dict)

    "AARDVARK": {
        "bio_e": 60,
        "original": {"size_level": 5, "length_in": 48, "weight_lbs": 40, "build": "Medium"},
        "mutant_changes_text": (
            "Aardvarks are anteater-like insectivores adapted to feeding on ants/termites; built for digging; long sticky tongue."
        ),
        "attribute_bonuses": {"PS": 2, "PP": 1, "PE": 2},
        "natural_weapons": [{"name": "Claws (1D6 damage)", "cost": 5, "details": "Claws: 1D6"}],
        "abilities": [
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced olfactory sense."},
            {"name": "Digging", "cost": 5, "details": "Digging ability."},
            {"name": "Tunneling", "cost": 10, "details": "Tunneling ability."},
        ],
    },

    "ALLIGATOR & CROCODILE": {
        "bio_e": 40,
        "original": {"size_level": 9, "length_in": 240, "weight_lbs": 175, "build": "Long"},
        "mutant_changes_text": (
            "Large swamp-dwelling carnivorous reptiles with protective scales and long jaws of conical teeth."
        ),
        "attribute_bonuses": {"PS": 3, "PE": 1, "Spd": 1},
        "natural_weapons": [
            {"name": "Teeth (1D8 damage)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12 damage)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Quick Run (1/min)", "cost": 10, "details": "Double move as a move action; +2 Initiative & Dodge for rest of round."},
            {"name": "Hold Breath", "cost": 5, "details": "Can hold breath for extended periods."},
            {"name": "Nightvision", "cost": 5, "details": "See in low light/darkness."},
            {"name": "Natural Armor: Light (AR 8, +20 SDC)", "cost": 10, "details": "AR 8; +20 SDC."},
            {"name": "Natural Armor: Medium (AR 10, +40 SDC)", "cost": 20, "details": "AR 10; +40 SDC."},
            {"name": "Natural Armor: Heavy (AR 12, +60 SDC)", "cost": 30, "details": "AR 12; +60 SDC."},
            {"name": "Natural Swimmer", "cost": 5, "details": "Swimming skill or +20%."},
        ],
    },

    "AMPHIBIANS — FROG & TOAD": {
        "bio_e": 80,
        "original": {"size_level": 2, "length_in": 12, "weight_lbs": 3, "build": "Medium"},
        "mutant_changes_text": (
            "Many species; aquatic or ground/tree. Insect-eaters with sticky tongues; some secrete toxins."
        ),
        "attribute_bonuses": {"PP": 2, "Spd": 2},
        "natural_weapons": [],
        "abilities": [
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Master Swimmer", "cost": 5, "details": "Swimming skill or +20%; survives depths to 400 ft."},
            {"name": "Hold Breath", "cost": 5, "details": "Hold breath for extended periods."},
            {"name": "Poison Touch", "cost": 15, "details": "Save vs Poison; fail: 1D6 HP + paralysis 1D6 rounds; success: -1 S/P/D 1D6 rounds; cumulative."},
        ],
    },

    "AMPHIBIANS — SALAMANDER, NEWT, & AXOLOTL": {
        "bio_e": 70,
        "original": {"size_level": 2, "length_in": 29, "weight_lbs": 5.5, "build": "Long"},
        "mutant_changes_text": (
            "Smooth-skinned long-tailed amphibians; famed for regeneration. Terrestrial near water, semi-aquatic, or primarily aquatic."
        ),
        "attribute_bonuses": {"PP": 1, "PE": 2},
        "natural_weapons": [{"name": "Teeth (1D6 damage)", "cost": 5, "details": "Bite: 1D6"}],
        "abilities": [
            {"name": "Regeneration (automatic)", "cost": 0, "details": "Regrows limbs/organs; +20% save vs coma/death; recover 1 HP + 3 SDC per hour; severe injury effects temporary (6D6 hours)."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Ultraviolet Vision", "cost": 5, "details": "Can see UV spectrum."},
            {"name": "Master Swimmer", "cost": 10, "details": "Swimming skill or +20%; survives depths to 400 ft."},
            {"name": "Gills", "cost": 5, "details": "Breathes underwater."},
        ],
    },

    "APES — CHIMPANZEE": {
        "bio_e": 25,
        "original": {"size_level": 8, "length_in": 60, "weight_lbs": 175, "build": "Medium"},
        "mutant_changes_text": (
            "Great apes are closest relatives to humans; already have partial hands/upright stance/human-like looks. Attribute bonus text garbled in source."
        ),
        "attribute_bonuses": {},
        "natural_weapons": [{"name": "Fists (1D6 damage)", "cost": 5, "details": "Punch/fist: 1D6"}],
        "abilities": [
            {"name": "Advanced Touch", "cost": 5, "details": "Enhanced tactile sensitivity."},
            {"name": "Prehensile Feet", "cost": 5, "details": "Feet function as partial hands."},
        ],
    },

    "APES — GORILLA": {
        "bio_e": 10,
        "original": {"size_level": 11, "length_in": 72, "weight_lbs": 800, "build": "Medium"},
        "mutant_changes_text": "Gorilla baseline; weight listed as 200–800 (roll 2D4×100). Attribute bonuses garbled in source.",
        "attribute_bonuses": {},
        "natural_weapons": [{"name": "Fists (1D6 damage)", "cost": 5, "details": "Punch/fist: 1D6"}],
        "abilities": [
            {"name": "Advanced Touch", "cost": 5, "details": "Enhanced tactile sensitivity."},
            {"name": "Prehensile Feet", "cost": 5, "details": "Feet function as partial hands."},
        ],
    },

    "APES — ORANGUTAN": {
        "bio_e": 20,
        "original": {"size_level": 9, "length_in": 54, "weight_lbs": 150, "build": "Medium"},
        "mutant_changes_text": "Orangutan baseline; attribute bonuses garbled in source (mentions social/mental boosts and PS +2 but unclear).",
        "attribute_bonuses": {},
        "natural_weapons": [{"name": "Fists (1D6 damage)", "cost": 5, "details": "Punch/fist: 1D6"}],
        "abilities": [
            {"name": "Advanced Touch", "cost": 5, "details": "Enhanced tactile sensitivity."},
            {"name": "Prehensile Feet", "cost": 5, "details": "Feet function as partial hands."},
        ],
    },

    "ARMADILLO": {
        "bio_e": 60,
        "original": {"size_level": 5, "length_in": 36, "weight_lbs": 30, "build": "Medium"},
        "mutant_changes_text": "Naturally armored mammal (nine-banded armadillo). Length listed as 2 ft + 1 ft tail; weight 20–30 lbs.",
        "attribute_bonuses": {"PS": 2, "PE": 3},
        "natural_weapons": [{"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; useful for climbing."}],
        "abilities": [
            {"name": "Natural Armor: Light (AR 10, +20 SDC)", "cost": 5, "details": "AR 10; +20 SDC."},
            {"name": "Natural Armor: Medium (AR 12, +40 SDC)", "cost": 10, "details": "AR 12; +40 SDC."},
            {"name": "Natural Armor: Heavy (AR 14, +60 SDC)", "cost": 20, "details": "AR 14; +60 SDC."},
            {"name": "Digging", "cost": 5, "details": "Digging ability."},
            {"name": "Tunneling", "cost": 10, "details": "Tunneling ability."},
        ],
    },

    "BADGER": {
        "bio_e": 65,
        "original": {"size_level": 4, "length_in": 28, "weight_lbs": 16, "build": "Short"},
        "mutant_changes_text": "Squat carnivores that dig into underground nests of prey.",
        "attribute_bonuses": {"PS": 3, "PP": 1, "PE": 4},
        "natural_weapons": [
            {"name": "Claws (1D8)", "cost": 5, "details": "Claws: 1D8"},
            {"name": "Teeth (1D8)", "cost": 75, "details": "Bite: 1D8 (cost appears unusually high; kept as written)."},
        ],
        "abilities": [
            {"name": "Poison Resistance", "cost": 5, "details": "Bonus to save vs venoms/poisons."},
            {"name": "Digging", "cost": 5, "details": "Digging ability."},
            {"name": "Tunneling", "cost": 10, "details": "Tunneling ability."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
        ],
    },

    "BAT": {
        "bio_e": 70,
        "original": {"size_level": 1, "length_in": 24, "weight_lbs": 2.25, "build": "Medium"},
        "mutant_changes_text": "Flying mammals; sonar is useful because they are nocturnal and live in dark caves. Length is wingspan (1–2 ft).",
        "attribute_bonuses": {"IQ": 1, "ME": 1, "PP": 2},
        "natural_weapons": [
            {"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
        ],
        "abilities": [
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Sonar", "cost": 5, "details": "Echolocation/sonar."},
        ],
    },

    "BEAR — BLACK BEAR": {
        "bio_e": 15,
        "original": {"size_level": 14, "length_in": None, "weight_lbs": 400, "build": "Medium"},
        "mutant_changes_text": "Bear baseline (black bear). Weight 300–400 lbs. Build not stated in source; treated as Medium.",
        "attribute_bonuses": {"PS": 8, "PP": 1, "PE": 4, "Spd": 4},
        "natural_weapons": [
            {"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Claws (1D10) (climbing)", "cost": 10, "details": "Claws: 1D10; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Hold Breath", "cost": 10, "details": "Hold Breath (note: polar bear version costs 5 in source)."},
            {"name": "Thick Skin (+20 SDC)", "cost": 5, "details": "+20 SDC."},
            {"name": "Advanced Sight", "cost": 5, "details": "Enhanced vision."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "BEAR — GRIZZLY": {
        "bio_e": 10,
        "original": {"size_level": 16, "length_in": None, "weight_lbs": 600, "build": "Medium"},
        "mutant_changes_text": "Grizzly bear; uses same Natural Weapons/Abilities as Black Bear entry.",
        "attribute_bonuses": {"PS": 8, "PP": 1, "PE": 4, "Spd": 4},
        "natural_weapons": [
            {"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Claws (1D10) (climbing)", "cost": 10, "details": "Claws: 1D10; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Hold Breath", "cost": 10, "details": "Hold Breath (note: polar bear version costs 5 in source)."},
            {"name": "Thick Skin (+20 SDC)", "cost": 5, "details": "+20 SDC."},
            {"name": "Advanced Sight", "cost": 5, "details": "Enhanced vision."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "BEAR — BROWN (KODIAK)": {
        "bio_e": 5,
        "original": {"size_level": 17, "length_in": None, "weight_lbs": 900, "build": "Medium"},
        "mutant_changes_text": "Brown/Kodiak bear; uses same Natural Weapons/Abilities as Black Bear entry.",
        "attribute_bonuses": {"PS": 8, "PP": 1, "PE": 4, "Spd": 4},
        "natural_weapons": [
            {"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Claws (1D10) (climbing)", "cost": 10, "details": "Claws: 1D10; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Hold Breath", "cost": 10, "details": "Hold Breath (note: polar bear version costs 5 in source)."},
            {"name": "Thick Skin (+20 SDC)", "cost": 5, "details": "+20 SDC."},
            {"name": "Advanced Sight", "cost": 5, "details": "Enhanced vision."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "BEAR — POLAR": {
        "bio_e": 0,
        "original": {"size_level": 18, "length_in": 108, "weight_lbs": 1000, "build": "Medium"},
        "mutant_changes_text": "Polar bear; same as bear baseline, except Hold Breath costs 5 Bio-E per note.",
        "attribute_bonuses": {"PS": 8, "PP": 1, "PE": 4, "Spd": 4},
        "natural_weapons": [
            {"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Claws (1D10) (climbing)", "cost": 10, "details": "Claws: 1D10; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Hold Breath", "cost": 5, "details": "Hold Breath (polar bear special cost note)."},
            {"name": "Thick Skin (+20 SDC)", "cost": 5, "details": "+20 SDC."},
            {"name": "Advanced Sight", "cost": 5, "details": "Enhanced vision."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "BEAVER": {
        "bio_e": 50,
        "original": {"size_level": 6, "length_in": 48, "weight_lbs": 60, "build": "Short"},
        "mutant_changes_text": "Dam-building rodent with wide flat tail; 'natural engineers' and family oriented.",
        "attribute_bonuses": {"IQ": 2, "ME": 2, "MA": 2, "PS": 2},
        "natural_weapons": [
            {"name": "Claws (1D6)", "cost": 5, "details": "Claws: 1D6"},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12) + Gnawing Teeth", "cost": 10, "details": "Bite: 1D12; can chew wood/clay/crumbly stone 1 in/round; hard plastics/ceramics/concrete/mortar at half speed."},
        ],
        "abilities": [
            {"name": "Digging (automatic)", "cost": 0, "details": "Digging is automatic."},
            {"name": "Tunneling", "cost": 5, "details": "Tunneling ability."},
            {"name": "Advanced Excavating", "cost": 10, "details": "Instinctive permanent structures; double normal time."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Touch", "cost": 5, "details": "Enhanced tactile sense."},
            {"name": "Natural Swimmer", "cost": 5, "details": "Swimming skill or +20%."},
            {"name": "Hold Breath", "cost": 5, "details": "Hold breath for extended periods."},
        ],
    },

    "BIRDS — CHICKEN": {
        "bio_e": 75,
        "original": {"size_level": 3, "length_in": 12, "weight_lbs": 10, "build": "Short"},
        "mutant_changes_text": "Domesticated; bred for food/eggs; one of the few that can see ultraviolet.",
        "attribute_bonuses": {},
        "natural_weapons": [
            {"name": "Talons (1D6)", "cost": 5, "details": "Talons: 1D6"},
            {"name": "Beak (1D6)", "cost": 5, "details": "Beak: 1D6"},
        ],
        "abilities": [
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
            {"name": "Ultraviolet Vision", "cost": 5, "details": "Can see UV spectrum."},
        ],
    },

    "BIRDS — CROW / RAVEN": {
        "bio_e": 70,
        "original": {"size_level": 3, "length_in": 24, "weight_lbs": 8, "build": "Medium"},
        "mutant_changes_text": "Intelligent social scavengers; live off crops/foraging. Includes noise/voice mimicry notes.",
        "attribute_bonuses": {"IQ": 4, "ME": 2},
        "natural_weapons": [
            {"name": "Talons (1D6) (climbing)", "cost": 5, "details": "Talons: 1D6; climbing."},
            {"name": "Beak (1D8)", "cost": 5, "details": "Beak: 1D8"},
        ],
        "abilities": [
            {"name": "Noise Mimicry / Effects", "cost": 0, "details": "Imitate noises; with full speech can imitate voices; +20% Impersonation bonus but still need skill."},
            {"name": "Flight", "cost": 10, "details": "True flight."},
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
        ],
    },

    "BIRDS — PARROT": {
        "bio_e": 70,
        "original": {"size_level": 3, "length_in": 24, "weight_lbs": 8, "build": "Medium"},
        "mutant_changes_text": "Colorful birds; many imitate voices. Uses same weapons/abilities pattern as Crow/Raven (including mimicry).",
        "attribute_bonuses": {"IQ": 2, "MA": 2, "PB": 2},
        "natural_weapons": [
            {"name": "Talons (1D6) (climbing)", "cost": 5, "details": "Talons: 1D6; climbing."},
            {"name": "Beak (1D8)", "cost": 5, "details": "Beak: 1D8"},
        ],
        "abilities": [
            {"name": "Noise Mimicry / Effects", "cost": 0, "details": "Imitate noises; with full speech can imitate voices; +20% Impersonation bonus but still need skill."},
            {"name": "Flight", "cost": 10, "details": "True flight."},
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
        ],
    },

    "BIRDS — DUCK": {
        "bio_e": 75,
        "original": {"size_level": 3, "length_in": 24, "weight_lbs": 15, "build": "Medium"},
        "mutant_changes_text": "Duck baseline (waterfowl). Hold Breath is automatic.",
        "attribute_bonuses": {"PE": 2},
        "natural_weapons": [
            {"name": "Talons (1D6)", "cost": 5, "details": "Talons: 1D6"},
            {"name": "Beak (1D6)", "cost": 5, "details": "Beak: 1D6"},
        ],
        "abilities": [
            {"name": "Hold Breath (automatic)", "cost": 0, "details": "Hold breath is automatic."},
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Natural Swimmer", "cost": 5, "details": "Swimming skill or +20%."},
            {"name": "Float", "cost": 5, "details": "Can sleep/rest floating on water."},
            {"name": "Insulating Water-Repellent Feathers", "cost": 5, "details": "Cold does half damage; +10 SDC."},
        ],
    },

    "BIRDS — GOOSE": {
        "bio_e": 70,
        "original": {"size_level": 4, "length_in": 36, "weight_lbs": 25, "build": "Medium"},
        "mutant_changes_text": "Goose (same waterfowl package as Duck).",
        "attribute_bonuses": {"MA": 2},
        "natural_weapons": [
            {"name": "Talons (1D6)", "cost": 5, "details": "Talons: 1D6"},
            {"name": "Beak (1D6)", "cost": 5, "details": "Beak: 1D6"},
        ],
        "abilities": [
            {"name": "Hold Breath (automatic)", "cost": 0, "details": "Hold breath is automatic."},
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Natural Swimmer", "cost": 5, "details": "Swimming skill or +20%."},
            {"name": "Float", "cost": 5, "details": "Can sleep/rest floating on water."},
            {"name": "Insulating Water-Repellent Feathers", "cost": 5, "details": "Cold does half damage; +10 SDC."},
        ],
    },

    "BIRDS — SWAN": {
        "bio_e": 65,
        "original": {"size_level": 5, "length_in": 60, "weight_lbs": 40, "build": "Medium"},
        "mutant_changes_text": "Swan (same waterfowl package as Duck).",
        "attribute_bonuses": {"PB": 3},
        "natural_weapons": [
            {"name": "Talons (1D6)", "cost": 5, "details": "Talons: 1D6"},
            {"name": "Beak (1D6)", "cost": 5, "details": "Beak: 1D6"},
        ],
        "abilities": [
            {"name": "Hold Breath (automatic)", "cost": 0, "details": "Hold breath is automatic."},
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Natural Swimmer", "cost": 5, "details": "Swimming skill or +20%."},
            {"name": "Float", "cost": 5, "details": "Can sleep/rest floating on water."},
            {"name": "Insulating Water-Repellent Feathers", "cost": 5, "details": "Cold does half damage; +10 SDC."},
        ],
    },

    "BIRDS — HAWK / FALCON": {
        "bio_e": 70,
        "original": {"size_level": 3, "length_in": 24, "weight_lbs": 15, "build": "Medium"},
        "mutant_changes_text": "Predatory birds with curved beaks/talons/sharp eyesight; dive attacks. Beak line truncated in source.",
        "attribute_bonuses": {"PS": 2, "PP": 4, "Spd": 2},
        "natural_weapons": [
            {"name": "Talons (1D8) (climbing)", "cost": 5, "details": "Talons: 1D8; climbing."},
            {"name": "Talons (1D10) (climbing)", "cost": 10, "details": "Talons: 1D10; climbing."},
        ],
        "abilities": [],
    },

    "BIRDS — EAGLE": {
        "bio_e": 65,
        "original": {"size_level": 4, "length_in": 36, "weight_lbs": 25, "build": "Medium"},
        "mutant_changes_text": "Eagle; other features match Hawk/Falcon block; abilities text broken in source at this point.",
        "attribute_bonuses": {"PS": 6, "PP": 2, "PB": 2},
        "natural_weapons": [
            {"name": "Talons (1D8) (climbing)", "cost": 5, "details": "Talons: 1D8; climbing."},
            {"name": "Talons (1D10) (climbing)", "cost": 10, "details": "Talons: 1D10; climbing."},
        ],
        "abilities": [],
    },

    "BIRDS — PENGUIN": {
        "bio_e": 53,
        "original": {"size_level": 7, "length_in": 42, "weight_lbs": 90, "build": "Short"},
        "mutant_changes_text": "Flightless diving birds adapted to cold climates; smaller temperate species exist.",
        "attribute_bonuses": {"MA": 2, "PE": 2},
        "natural_weapons": [{"name": "Beak (1D6)", "cost": 5, "details": "Beak: 1D6"}],
        "abilities": [
            {"name": "Hold Breath (automatic)", "cost": 0, "details": "Hold breath is automatic."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Ultraviolet Vision", "cost": 5, "details": "Can see UV spectrum."},
            {"name": "Insulating Water-Repellent Feathers", "cost": 5, "details": "Cold does half damage; +10 SDC."},
            {"name": "Master Swimmer", "cost": 5, "details": "Swimming skill or +20%; survive depths to 500 ft."},
        ],
    },

    "BIRDS — PIGEON": {
        "bio_e": 85,
        "original": {"size_level": 2, "length_in": 12, "weight_lbs": 3, "build": "Medium"},
        "mutant_changes_text": "Pigeon baseline for city birds/doves/game birds. Beak damage unclear in source line.",
        "attribute_bonuses": {"PE": 4},
        "natural_weapons": [
            {"name": "Talons (1D4) (climbing)", "cost": 5, "details": "Talons: 1D4; climbing."},
            {"name": "Beak (damage unclear)", "cost": 5, "details": "Beak damage not clearly stated in source line."},
        ],
        "abilities": [
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Advanced Vision", "cost": 10, "details": "Enhanced eyesight."},
        ],
    },

    "BIRDS — DOVE": {
        "bio_e": 90,
        "original": {"size_level": 1, "length_in": 12, "weight_lbs": 3, "build": "Medium"},
        "mutant_changes_text": "Dove variant (same package as Pigeon).",
        "attribute_bonuses": {"PE": 2, "PB": 2},
        "natural_weapons": [
            {"name": "Talons (1D4) (climbing)", "cost": 5, "details": "Talons: 1D4; climbing."},
            {"name": "Beak (damage unclear)", "cost": 5, "details": "Beak damage not clearly stated in source line."},
        ],
        "abilities": [
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Advanced Vision", "cost": 10, "details": "Enhanced eyesight."},
        ],
    },

    "BIRDS — WILD GAME BIRDS (GROUSE / PARTRIDGE / PHEASANT / QUAIL)": {
        "bio_e": 80,
        "original": {"size_level": 3, "length_in": 36, "weight_lbs": 20, "build": "Medium"},
        "mutant_changes_text": "Wild game bird variant (same package as Pigeon).",
        "attribute_bonuses": {"PE": 2, "Spd": 2},
        "natural_weapons": [
            {"name": "Talons (1D4) (climbing)", "cost": 5, "details": "Talons: 1D4; climbing."},
            {"name": "Beak (damage unclear)", "cost": 5, "details": "Beak damage not clearly stated in source line."},
        ],
        "abilities": [
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Advanced Vision", "cost": 10, "details": "Enhanced eyesight."},
        ],
    },

    "BIRDS — SMALL WILD BIRDS": {
        "bio_e": 90,
        "original": {"size_level": 1, "length_in": 12, "weight_lbs": 1.25, "build": "Medium"},
        "mutant_changes_text": "Small birds that feed on grains/seeds/fruits/insects; includes many urban/suburban forest species.",
        "attribute_bonuses": {"PP": 2, "Spd": 2},
        "natural_weapons": [
            {"name": "Talons (1D4) (climbing)", "cost": 5, "details": "Talons: 1D4; climbing."},
            {"name": "Beak (1D6)", "cost": 5, "details": "Beak: 1D6"},
        ],
        "abilities": [
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
        ],
    },

    "BIRDS — TEMPERATE SONGBIRDS": {
        "bio_e": 80,
        "original": {"size_level": 1, "length_in": 12, "weight_lbs": 1.25, "build": "Medium"},
        "mutant_changes_text": "Temperate songbirds.",
        "attribute_bonuses": {"MA": 2, "PP": 2, "Spd": 2},
        "natural_weapons": [
            {"name": "Talons (1D4) (climbing)", "cost": 5, "details": "Talons: 1D4; climbing."},
            {"name": "Beak (1D6)", "cost": 5, "details": "Beak: 1D6"},
        ],
        "abilities": [
            {"name": "Natural Singer (automatic)", "cost": 0, "details": "Sing skill or +20%."},
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
        ],
    },

    "BIRDS — TROPICAL SONGBIRDS": {
        "bio_e": 80,
        "original": {"size_level": 1, "length_in": 12, "weight_lbs": 1.25, "build": "Medium"},
        "mutant_changes_text": "Tropical songbirds.",
        "attribute_bonuses": {"PP": 2, "PB": 2, "Spd": 2},
        "natural_weapons": [
            {"name": "Talons (1D4) (climbing)", "cost": 5, "details": "Talons: 1D4; climbing."},
            {"name": "Beak (1D6)", "cost": 5, "details": "Beak: 1D6"},
        ],
        "abilities": [
            {"name": "Natural Singer (automatic)", "cost": 0, "details": "Sing skill or +20%."},
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
        ],
    },

    "BIRDS — TURKEY": {
        "bio_e": 60,
        "original": {"size_level": 5, "length_in": 48, "weight_lbs": 40, "build": "Medium"},
        "mutant_changes_text": "Domestic turkey is flightless and bred for food; wild turkeys are leaner/faster and can fly.",
        "attribute_bonuses": {"PP": 2, "Spd": 6},
        "natural_weapons": [
            {"name": "Talons (1D6)", "cost": 5, "details": "Talons: 1D6"},
            {"name": "Spurs (1D10)", "cost": 10, "details": "Spurs: 1D10"},
            {"name": "Beak (1D6)", "cost": 5, "details": "Beak: 1D6"},
        ],
        "abilities": [
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Flight", "cost": 20, "details": "True flight."},
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
        ],
    },

    "BUFFALO & BISON": {
        "bio_e": 0,
        "original": {"size_level": 19, "length_in": 132, "weight_lbs": 2000, "build": "Medium"},
        "mutant_changes_text": "Bison are huge North American grazers with a shoulder hump; true buffalo are Africa/Asia and lack the hump.",
        "attribute_bonuses": {"PS": 6, "Spd": 4},
        "natural_weapons": [{"name": "Horns (1D8)", "cost": 5, "details": "Horns: 1D8"}],
        "abilities": [
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Thick Skin (+20 SDC)", "cost": 5, "details": "+20 SDC."},
        ],
    },

    "CAMEL": {
        "bio_e": 0,
        "original": {"size_level": 18, "length_in": 132, "weight_lbs": 1000, "build": "Medium"},
        "mutant_changes_text": "Desert pack animals known for water storage; often short-tempered.",
        "attribute_bonuses": {"PS": 2, "PE": 4, "Spd": 6},
        "natural_weapons": [{"name": "Teeth (1D6)", "cost": 5, "details": "Bite: 1D6"}],
        "abilities": [
            {"name": "Spit", "cost": 5, "details": "12 ft; +2 Strike; called shot to eyes blinds 1D4 rounds."},
            {"name": "Water Storage", "cost": 10, "details": "2 days per gallon; store up to 10 gallons; drink/store in 12 minutes."},
        ],
    },

    "CANINES — DOGS": {
        "bio_e": 65,
        "original": {"size_level": None, "length_in": None, "weight_lbs": None, "build": "Medium"},
        "mutant_changes_text": (
            "Many breeds; baseline is average mongrel. Bio-E: 65 (reduce by 5 for each step above Size Level 3). "
            "Attribute bonuses vary by size: SL 3–5: IQ+2 MA+2 PP+2 Spd+2; SL 6–8: IQ+2 MA+2 PS+2 Spd+2."
        ),
        "attribute_bonuses": {},
        "natural_weapons": [
            {"name": "Teeth (1D6)", "cost": 5, "details": "Bite: 1D6"},
            {"name": "Teeth (1D10)", "cost": 10, "details": "Bite: 1D10"},
        ],
        "abilities": [
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Advanced Hearing", "cost": 10, "details": "Enhanced hearing."},
            {"name": "Nightvision", "cost": 10, "details": "See in darkness/low light."},
            {"name": "Digging", "cost": 10, "details": "Digging ability."},
            {"name": "Natural Swimmer", "cost": 10, "details": "Swimming skill or +20%."},
        ],
    },

    "CANINES — FOX": {
        "bio_e": 60,
        "original": {"size_level": 3, "length_in": 40, "weight_lbs": 10, "build": "Long"},
        "mutant_changes_text": "Fox baseline (red/gray/arctic similar). Build spelled 'Lone' in source.",
        "attribute_bonuses": {"IQ": 2, "ME": 4, "PB": 2, "Spd": 6},
        "natural_weapons": [
            {"name": "Teeth (1D6)", "cost": 5, "details": "Bite: 1D6"},
            {"name": "Teeth (1D10)", "cost": 10, "details": "Bite: 1D10"},
        ],
        "abilities": [
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Digging", "cost": 10, "details": "Digging ability."},
        ],
    },

    "CANINES — COYOTE": {
        "bio_e": 55,
        "original": {"size_level": 5, "length_in": 54, "weight_lbs": 40, "build": "Medium"},
        "mutant_changes_text": "Coyote baseline; other features are same as wolf block per source note.",
        "attribute_bonuses": {"IQ": 2, "ME": 2, "PP": 2, "PE": 2, "Spd": 6},
        "natural_weapons": [
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Digging (Coyotes only)", "cost": 10, "details": "Digging ability."},
        ],
    },

    "CANINES — WOLF": {
        "bio_e": 45,
        "original": {"size_level": 8, "length_in": 72, "weight_lbs": 150, "build": "Medium"},
        "mutant_changes_text": "Wolf baseline.",
        "attribute_bonuses": {"IQ": 2, "MA": 2, "PS": 4, "PP": 2, "Spd": 4},
        "natural_weapons": [
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Vision (Wolves only)", "cost": 5, "details": "Enhanced eyesight."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "CATTLE — COW": {
        "bio_e": 10,
        "original": {"size_level": 16, "length_in": 96, "weight_lbs": 2000, "build": "Short"},
        "mutant_changes_text": "Domesticated meat/milk cattle; many breeds.",
        "attribute_bonuses": {"PS": 2, "PE": 4, "Spd": 2},
        "natural_weapons": [{"name": "Horns (1D6)", "cost": 5, "details": "Horns: 1D6"}],
        "abilities": [
            {"name": "Advanced Hearing", "cost": 10, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 10, "details": "Enhanced smell."},
        ],
    },

    "CATTLE — BULL": {
        "bio_e": 10,
        "original": {"size_level": 16, "length_in": 96, "weight_lbs": 2000, "build": "Short"},
        "mutant_changes_text": "Bull variant (same baseline as cow).",
        "attribute_bonuses": {"PS": 4, "PE": 2, "Spd": 4},
        "natural_weapons": [
            {"name": "Horns (1D6)", "cost": 5, "details": "Horns: 1D6"},
            {"name": "Horns (1D12) (Bulls only)", "cost": 10, "details": "Horns: 1D12"},
        ],
        "abilities": [
            {"name": "Advanced Hearing", "cost": 10, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 10, "details": "Enhanced smell."},
        ],
    },

    "DEER": {
        "bio_e": 30,
        "original": {"size_level": 13, "length_in": 72, "weight_lbs": 400, "build": "Medium"},
        "mutant_changes_text": "Deer baseline (hands/biped/speech/looks shared within deer/elk/moose block per source).",
        "attribute_bonuses": {"PP": 2, "PE": 2, "Spd": 6},
        "natural_weapons": [
            {"name": "Antlers (Small damage) (bucks only)", "cost": 5, "details": "Antlers (small damage)"},
            {"name": "Antlers (Large damage) (bucks only)", "cost": 10, "details": "Antlers (large damage)"},
        ],
        "abilities": [
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Advanced Taste", "cost": 5, "details": "Enhanced taste."},
        ],
    },

    "ELK": {
        "bio_e": 10,
        "original": {"size_level": 17, "length_in": 108, "weight_lbs": 1100, "build": "Medium"},
        "mutant_changes_text": "Elk baseline (deer family block).",
        "attribute_bonuses": {"PS": 2, "PE": 2, "Spd": 6},
        "natural_weapons": [
            {"name": "Antlers (Small damage) (bulls only)", "cost": 5, "details": "Antlers (small damage)"},
            {"name": "Antlers (Large damage) (bulls only)", "cost": 10, "details": "Antlers (large damage)"},
        ],
        "abilities": [
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Advanced Taste", "cost": 5, "details": "Enhanced taste."},
        ],
    },

    "MOOSE": {
        "bio_e": 0,
        "original": {"size_level": 19, "length_in": 120, "weight_lbs": 1500, "build": "Medium"},
        "mutant_changes_text": "Moose baseline (deer family block).",
        "attribute_bonuses": {"PS": 4, "PE": 2, "Spd": 2},
        "natural_weapons": [
            {"name": "Antlers (Small damage) (bulls only)", "cost": 5, "details": "Antlers (small damage)"},
            {"name": "Antlers (Large damage) (bulls only)", "cost": 10, "details": "Antlers (large damage)"},
        ],
        "abilities": [
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Advanced Taste", "cost": 5, "details": "Enhanced taste."},
        ],
    },

    "ELEPHANT": {
        "bio_e": 0,
        "original": {"size_level": 20, "length_in": 120, "weight_lbs": 10000, "build": "Short"},
        "mutant_changes_text": "Largest land animal; strong; trunk functions as flexible prehensile limb.",
        "attribute_bonuses": {"IQ": 4, "MA": 2, "PS": 4},
        "natural_weapons": [
            {"name": "Tusks (1D8)", "cost": 5, "details": "Tusks: 1D8"},
            {"name": "Tusks (1D12)", "cost": 10, "details": "Tusks: 1D12"},
        ],
        "abilities": [
            {"name": "Prehensile Trunk", "cost": 5, "details": "Extra limb; counts as Partial Hand; long enough to touch ground."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Thick Skin (+20 SDC)", "cost": 5, "details": "+20 SDC."},
        ],
    },

    "FELINES — BOBCAT": {
        "bio_e": 70,
        "original": {"size_level": 5, "length_in": 42, "weight_lbs": 22, "build": "Short"},
        "mutant_changes_text": "Bobcat (feline block; other features match Lynx per note).",
        "attribute_bonuses": {"ME": 2, "PP": 4, "Spd": 4},
        "natural_weapons": [
            {"name": "Retractable Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Retractable Claws (1D10) (climbing)", "cost": 10, "details": "Claws: 1D10; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
        ],
        "abilities": [
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "FELINES — LYNX": {
        "bio_e": 65,
        "original": {"size_level": 5, "length_in": 40, "weight_lbs": 35, "build": "Short"},
        "mutant_changes_text": "Lynx baseline.",
        "attribute_bonuses": {"ME": 2, "PP": 4, "Spd": 4},
        "natural_weapons": [
            {"name": "Retractable Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Retractable Claws (1D10) (climbing)", "cost": 10, "details": "Claws: 1D10; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
        ],
        "abilities": [
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "FELINES — CAT": {
        "bio_e": 75,
        "original": {"size_level": 3, "length_in": 24, "weight_lbs": 10, "build": "Medium"},
        "mutant_changes_text": "Domesticated cat; markings vary.",
        "attribute_bonuses": {"MA": 2, "PP": 4, "Spd": 4},
        "natural_weapons": [
            {"name": "Retractable Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
        ],
        "abilities": [
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "FELINES — CHEETAH": {
        "bio_e": 45,
        "original": {"size_level": 8, "length_in": 60, "weight_lbs": 125, "build": "Long"},
        "mutant_changes_text": "Fastest mammals; sleek athletic build. Height listed (up to 30 inches tall).",
        "attribute_bonuses": {"PS": 1, "PP": 4, "PE": 2, "Spd": 10},
        "natural_weapons": [
            {"name": "Retractable Claws (1D6)", "cost": 5, "details": "Claws: 1D6"},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
        ],
        "abilities": [
            {"name": "Quick Run (1/min)", "cost": 10, "details": "Double move; +2 Initiative & Dodge for rest of round."},
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "FELINES — COUGAR": {
        "bio_e": 40,
        "original": {"size_level": 9, "length_in": 60, "weight_lbs": 175, "build": "Medium"},
        "mutant_changes_text": "Cougar baseline (great cats block).",
        "attribute_bonuses": {"ME": 2, "PS": 2, "PP": 4, "Spd": 4},
        "natural_weapons": [
            {"name": "Retractable Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Retractable Claws (1D10) (climbing)", "cost": 10, "details": "Claws: 1D10; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Natural Swimmer", "cost": 10, "details": "Swimming skill or +20%."},
        ],
    },

    "FELINES — JAGUAR / LEOPARD": {
        "bio_e": 23,
        "original": {"size_level": 12, "length_in": 72, "weight_lbs": 300, "build": "Medium"},
        "mutant_changes_text": "Jaguar/Leopard baseline (great cats block).",
        "attribute_bonuses": {"ME": 2, "PS": 3, "PP": 3, "Spd": 4},
        "natural_weapons": [
            {"name": "Retractable Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Retractable Claws (1D10) (climbing)", "cost": 10, "details": "Claws: 1D10; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Great Leaping", "cost": 10, "details": "Triple Jump distance (Jaguar/Leopard only)."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Natural Swimmer", "cost": 10, "details": "Swimming skill or +20%."},
        ],
    },

    "FELINES — LION": {
        "bio_e": 15,
        "original": {"size_level": 14, "length_in": None, "weight_lbs": None, "build": "Medium"},
        "mutant_changes_text": "Lion baseline. Weight unclear in source line; left as None.",
        "attribute_bonuses": {"MA": 2, "PS": 4, "PP": 2, "Spd": 3},
        "natural_weapons": [
            {"name": "Retractable Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Retractable Claws (1D10) (climbing)", "cost": 10, "details": "Claws: 1D10; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Natural Swimmer", "cost": 10, "details": "Swimming skill or +20%."},
        ],
    },

    "FELINES — TIGER": {
        "bio_e": 10,
        "original": {"size_level": 15, "length_in": None, "weight_lbs": 500, "build": "Medium"},
        "mutant_changes_text": "Tiger baseline.",
        "attribute_bonuses": {"PS": 6, "PP": 1, "PE": 1, "Spd": 2},
        "natural_weapons": [
            {"name": "Retractable Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Retractable Claws (1D10) (climbing)", "cost": 10, "details": "Claws: 1D10; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
            {"name": "Teeth (1D12)", "cost": 10, "details": "Bite: 1D12"},
        ],
        "abilities": [
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Natural Swimmer", "cost": 10, "details": "Swimming skill or +20%."},
        ],
    },

    "GOAT": {
        "bio_e": 55,
        "original": {"size_level": 6, "length_in": 10, "weight_lbs": 75, "build": "Medium"},
        "mutant_changes_text": "Domesticated milk/meat animal; hardy. Length line appears inconsistent (kept as written: 'up to 10 inches long').",
        "attribute_bonuses": {"IQ": 1, "ME": 1, "PE": 4, "Spd": 2},
        "natural_weapons": [{"name": "Horns (1D8)", "cost": 5, "details": "Horns: 1D8"}],
        "abilities": [
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Natural Climber", "cost": 5, "details": "Climbing skill or +20%."},
            {"name": "Toxin Resistance", "cost": 10, "details": "+5 save vs toxins/poisons/drugs."},
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
        ],
    },

    "HIPPOPOTAMUS": {
        "bio_e": 0,
        "original": {"size_level": 20, "length_in": 168, "weight_lbs": 4000, "build": "Short"},
        "mutant_changes_text": "Giant aggressive grazers; spend most of life in water.",
        "attribute_bonuses": {"ME": 2, "PS": 6, "PE": 2},
        "natural_weapons": [{"name": "Teeth (1D12)", "cost": 5, "details": "Bite: 1D12"}],
        "abilities": [
            {"name": "Thick Skin (+20 SDC)", "cost": 5, "details": "+20 SDC."},
            {"name": "Light Natural Armor (AR 8, +40 SDC)", "cost": 10, "details": "AR 8; +40 SDC."},
            {"name": "Natural Swimmer", "cost": 5, "details": "Swimming skill or +20%."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Hold Breath", "cost": 5, "details": "Hold breath for extended periods."},
        ],
    },

    "HORSE (RIDING HORSE)": {
        "bio_e": 10,
        "original": {"size_level": 18, "length_in": 60, "weight_lbs": 1400, "build": "Medium"},
        "mutant_changes_text": "Domesticated grazing animal; typical riding horse. Height listed as up to 60 inches at shoulder.",
        "attribute_bonuses": {"PS": 2, "PE": 2, "Spd": 8},
        "natural_weapons": [],
        "abilities": [
            {"name": "Leaping", "cost": 10, "details": "Double Jump distance."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
        ],
    },

    "LEMUR": {
        "bio_e": 60,
        "original": {"size_level": 3, "length_in": 42, "weight_lbs": 6, "build": "Long"},
        "mutant_changes_text": "Long-snouted primate from Madagascar (ring-tailed lemur baseline).",
        "attribute_bonuses": {"IQ": 1, "MA": 3, "PP": 2},
        "natural_weapons": [{"name": "Claws (1D6)", "cost": 5, "details": "Claws: 1D6"}],
        "abilities": [
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Nightvision", "cost": 10, "details": "See in darkness/low light."},
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Prehensile Feet (Partial Hands)", "cost": 5, "details": "Feet function as partial hands."},
        ],
    },

    "LIZARDS (GROUP ENTRY)": {
        "bio_e": 0,
        "original": {"size_level": None, "length_in": None, "weight_lbs": None, "build": "Long"},
        "mutant_changes_text": (
            "Group entry: Gecko/Skink (SL1), Chameleon/Horned Lizard (SL2), Gila Monster/Iguana (SL3), Komodo Dragon (SL13). "
            "Bio-E: 85/80/75/25 respectively; attribute bonuses vary by variant. This entry is kept as a group placeholder."
        ),
        "attribute_bonuses": {},
        "natural_weapons": [],
        "abilities": [],
    },

    "MARTEN & MINK": {
        "bio_e": 80,
        "original": {"size_level": 2, "length_in": 20, "weight_lbs": 3, "build": "Long"},
        "mutant_changes_text": "Larger cousins to weasels; long bodies; valuable fur. Martens are fox-faced climbers; minks live near water.",
        "attribute_bonuses": {"IQ": 2, "ME": 1, "PP": 2, "Spd": 5},
        "natural_weapons": [
            {"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
        ],
        "abilities": [
            {"name": "Tight Squeeze (automatic)", "cost": 0, "details": "Fit through openings a quarter their Size Level."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Nightvision", "cost": 10, "details": "See in darkness/low light."},
            {"name": "Advanced Smell", "cost": 10, "details": "Enhanced smell."},
        ],
    },

    "MOLE": {
        "bio_e": 80,
        "original": {"size_level": 1, "length_in": 6, "weight_lbs": 1, "build": "Short"},
        "mutant_changes_text": "Small furry burrowers adapted to underground life. Looks partial/full lines cut off in source.",
        "attribute_bonuses": {"IQ": 1, "PE": 2},
        "natural_weapons": [{"name": "Claws (1D6)", "cost": 5, "details": "Claws: 1D6"}],
        "abilities": [
            {"name": "Hold Breath (automatic)", "cost": 0, "details": "Hold breath is automatic."},
            {"name": "Digging (automatic)", "cost": 0, "details": "Digging is automatic."},
            {"name": "Tunneling", "cost": 5, "details": "Tunneling ability."},
            {"name": "Advanced Excavating", "cost": 10, "details": "Instinctive permanent structures; double time."},
            {"name": "Nightvision", "cost": 5, "details": "See in darkness/low light."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "MONKEY (ARBOREAL)": {
        "bio_e": 45,
        "original": {"size_level": 4, "length_in": 24, "weight_lbs": 20, "build": "Long"},
        "mutant_changes_text": "Arboreal monkeys (prehensile tails) kept as pets/research animals; markings vary.",
        "attribute_bonuses": {"IQ": 2, "ME": 2, "PP": 2, "PE": 2},
        "natural_weapons": [{"name": "Teeth (1D6)", "cost": 5, "details": "Bite: 1D6"}],
        "abilities": [
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
            {"name": "Nightvision", "cost": 10, "details": "See in darkness/low light."},
            {"name": "Advanced Touch", "cost": 5, "details": "Enhanced tactile sense."},
            {"name": "Prehensile Tail", "cost": 15, "details": "Extra limb; Partial Hand."},
            {"name": "Prehensile Feet (Partial Hands)", "cost": 5, "details": "Feet function as partial hands."},
        ],
    },

    "BABOON": {
        "bio_e": 35,
        "original": {"size_level": 6, "length_in": 36, "weight_lbs": 65, "build": "Medium"},
        "mutant_changes_text": "Ground-dwelling tribal monkeys; mandrills/geladas similar. Uses same ability package as Monkey (Arboreal) per source.",
        "attribute_bonuses": {"IQ": 2, "MA": 2, "PS": 4},
        "natural_weapons": [{"name": "Teeth (1D6)", "cost": 5, "details": "Bite: 1D6"}],
        "abilities": [
            {"name": "Advanced Vision", "cost": 5, "details": "Enhanced eyesight."},
            {"name": "Nightvision", "cost": 10, "details": "See in darkness/low light."},
            {"name": "Advanced Touch", "cost": 5, "details": "Enhanced tactile sense."},
            {"name": "Prehensile Tail", "cost": 15, "details": "Extra limb; Partial Hand."},
            {"name": "Prehensile Feet (Partial Hands)", "cost": 5, "details": "Feet function as partial hands."},
        ],
    },

    "MUSKRAT": {
        "bio_e": 75,
        "original": {"size_level": 2, "length_in": 25, "weight_lbs": 14, "build": "Short"},
        "mutant_changes_text": "River-dwelling vegetarians/scavengers; build dens with underwater entrances. Abilities not listed in source beyond gnawing note.",
        "attribute_bonuses": {"IQ": 3, "ME": 1, "MA": 1},
        "natural_weapons": [
            {"name": "Claws (1D6)", "cost": 5, "details": "Claws: 1D6"},
            {"name": "Teeth (damage unclear)", "cost": 5, "details": "Bite damage unclear in source line."},
            {"name": "Teeth (1D10) + Gnawing Teeth", "cost": 10, "details": "Bite: 1D10; gnawing per beaver-style chew rules."},
        ],
        "abilities": [],
    },

    "RABBIT": {
        "bio_e": 70,
        "original": {"size_level": 3, "length_in": 18, "weight_lbs": 8, "build": "Medium"},
        "mutant_changes_text": "Rabbits/hares worldwide; small vegetarians that depend on speed and agility.",
        "attribute_bonuses": {"PP": 2, "Spd": 8},
        "natural_weapons": [{"name": "Teeth (1D6)", "cost": 5, "details": "Bite: 1D6"}],
        "abilities": [
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Digging", "cost": 5, "details": "Digging ability."},
            {"name": "Tunneling", "cost": 10, "details": "Tunneling ability."},
            {"name": "Excavating", "cost": 15, "details": "Excavating ability."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "RACCOON": {
        "bio_e": 65,
        "original": {"size_level": 4, "length_in": 38, "weight_lbs": 18, "build": "Short"},
        "mutant_changes_text": "Adaptable nocturnal scavengers. Looks text partially truncated in source.",
        "attribute_bonuses": {"IQ": 2, "MA": 2, "PP": 2, "PE": 2},
        "natural_weapons": [{"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."}],
        "abilities": [
            {"name": "Nightvision", "cost": 10, "details": "See in darkness/low light."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "RHINOCEROS": {
        "bio_e": 0,
        "original": {"size_level": 20, "length_in": 78, "weight_lbs": 8000, "build": "Long"},
        "mutant_changes_text": "Aggressive grazing animals; good runners; very strong. African rhinos have two horns; Great Indian rhino has one.",
        "attribute_bonuses": {"PS": 4, "Spd": 4},
        "natural_weapons": [
            {"name": "Horn (1D8)", "cost": 5, "details": "Horn: 1D8"},
            {"name": "Horn (1D12)", "cost": 10, "details": "Horn: 1D12"},
        ],
        "abilities": [
            {"name": "Natural Armor: Light (AR 8, +20 SDC)", "cost": 10, "details": "AR 8; +20 SDC."},
            {"name": "Natural Armor: Medium (AR 10, +40 SDC)", "cost": 20, "details": "AR 10; +40 SDC."},
            {"name": "Natural Armor: Heavy (AR 12, +60 SDC)", "cost": 30, "details": "AR 12; +60 SDC."},
            {"name": "Natural Armor: Tough (AR 14, +80 SDC)", "cost": 40, "details": "AR 14; +80 SDC."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
        ],
    },

    "PIG": {
        "bio_e": 25,
        "original": {"size_level": 12, "length_in": 72, "weight_lbs": 800, "build": "Short"},
        "mutant_changes_text": "Domesticated pigs bred for meat production; can be very large.",
        "attribute_bonuses": {"IQ": 2, "MA": 2, "PS": 2, "PE": 2, "Spd": 4},
        "natural_weapons": [
            {"name": "Tusks (small, 1D6)", "cost": 5, "details": "Tusks: 1D6"},
            {"name": "Tusks (large, 1D10)", "cost": 10, "details": "Tusks: 1D10"},
        ],
        "abilities": [
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Thick Skin (+20 SDC)", "cost": 5, "details": "+20 SDC."},
        ],
    },

    "BOAR": {
        "bio_e": 25,
        "original": {"size_level": 12, "length_in": 72, "weight_lbs": 800, "build": "Short"},
        "mutant_changes_text": "Aggressive wild pigs; invasive; dangerous with tusks.",
        "attribute_bonuses": {"PS": 4, "PE": 4, "Spd": 4},
        "natural_weapons": [
            {"name": "Tusks (small, 1D6)", "cost": 5, "details": "Tusks: 1D6"},
            {"name": "Tusks (large, 1D10)", "cost": 10, "details": "Tusks: 1D10"},
        ],
        "abilities": [
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Thick Skin (+20 SDC)", "cost": 5, "details": "+20 SDC."},
        ],
    },

    "PORCUPINE": {
        "bio_e": 65,
        "original": {"size_level": 5, "length_in": 42, "weight_lbs": 40, "build": "Medium"},
        "mutant_changes_text": "Defensive quills; dangerous to predators.",
        "attribute_bonuses": {"ME": 2, "PE": 2},
        "natural_weapons": [
            {"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Teeth (1D8)", "cost": 5, "details": "Bite: 1D8"},
        ],
        "abilities": [
            {"name": "Quill Defense", "cost": 15, "details": "Natural Armor AR 12, +20 SDC; attackers rolling <12 take 1D12; mutant gets +1D12 on unarmed melee."},
            {"name": "Advanced Smell", "cost": 10, "details": "Enhanced smell."},
        ],
    },

    "RODENTS (GROUP ENTRY)": {
        "bio_e": 0,
        "original": {"size_level": None, "length_in": None, "weight_lbs": None, "build": "Medium"},
        "mutant_changes_text": (
            "Group entry: SL1 (Mice/Gerbils/Hamsters) Bio-E 85; SL2 (Rats/Guinea Pigs/Pikas) Bio-E 80. "
            "Attribute bonuses vary by subgroup. This entry is kept as a group placeholder."
        ),
        "attribute_bonuses": {},
        "natural_weapons": [],
        "abilities": [],
    },

    "SHARK (Tiger Shark baseline)": {
        "bio_e": 0,
        "original": {"size_level": 19, "length_in": 168, "weight_lbs": 1400, "build": "Long"},
        "mutant_changes_text": "Ancient aquatic apex predators; entry lists tiger shark baseline.",
        "attribute_bonuses": {"PS": 4, "PP": 2, "Spd": 2},
        "natural_weapons": [
            {"name": "Teeth (1D10)", "cost": 5, "details": "Bite: 1D10"},
            {"name": "Teeth (1D12+2)", "cost": 10, "details": "Bite: 1D12+2"},
        ],
        "abilities": [
            {"name": "Electrosense", "cost": 5, "details": "Detect electrical fields in water."},
            {"name": "Advanced Smell", "cost": 5, "details": "Enhanced smell."},
            {"name": "Gills", "cost": 5, "details": "Breathes underwater."},
            {"name": "Master Swimmer", "cost": 5, "details": "Swimming skill or +20%; depth line cut off in source."},
        ],
    },

    "SKUNK (Striped)": {
        "bio_e": 70,
        "original": {"size_level": 3, "length_in": 32, "weight_lbs": 8, "build": "Short"},
        "mutant_changes_text": "Striped skunk; uses stink glands as defense. Looks text mixed/truncated in source.",
        "attribute_bonuses": {"ME": 2, "PE": 2},
        "natural_weapons": [],
        "abilities": [
            {"name": "Stink Spray", "cost": 15, "details": "Butyl mercaptan musk w/ sulfuric acid; 8/day; 10 ft; failed Save vs Toxin = nausea/incapacitated 2D6 minutes; stench lasts 2D12 days; Advanced Smell = -4 to save."},
        ],
    },

    "SKUNK (Spotted)": {
        "bio_e": 75,
        "original": {"size_level": 2, "length_in": 20, "weight_lbs": 23, "build": "Short"},
        "mutant_changes_text": "Spotted skunk variant (same stink spray). Weight listed as 23 lbs in source (unusual; kept).",
        "attribute_bonuses": {"ME": 2, "PE": 2},
        "natural_weapons": [],
        "abilities": [
            {"name": "Stink Spray", "cost": 15, "details": "Butyl mercaptan musk w/ sulfuric acid; 8/day; 10 ft; failed Save vs Toxin = nausea/incapacitated 2D6 minutes; stench lasts 2D12 days; Advanced Smell = -4 to save."},
        ],
    },

    "SQUIRREL": {
        "bio_e": 80,
        "original": {"size_level": 1, "length_in": 20, "weight_lbs": 1, "build": "Long"},
        "mutant_changes_text": "Common urban wild mammal; great climbers. Flying squirrels can glide.",
        "attribute_bonuses": {"PP": 2, "Spd": 4},
        "natural_weapons": [
            {"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Teeth (1D6)", "cost": 5, "details": "Bite: 1D6"},
            {"name": "Teeth (1D10) + Gnawing Teeth", "cost": 10, "details": "Bite: 1D10; gnawing teeth."},
        ],
        "abilities": [
            {"name": "Digging (automatic)", "cost": 0, "details": "Digging is automatic."},
            {"name": "Tunneling", "cost": 10, "details": "Tunneling ability."},
            {"name": "Excavating", "cost": 20, "details": "Excavating ability."},
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Glide", "cost": 10, "details": "Gliding flight."},
            {"name": "Advanced Hearing", "cost": 5, "details": "Enhanced hearing."},
        ],
    },

    "TURTLES — POND TURTLE": {
        "bio_e": 90,
        "original": {"size_level": 1, "length_in": 5, "weight_lbs": 1, "build": "Medium"},
        "mutant_changes_text": "Many environments; TMNT mutated from small pond turtles.",
        "attribute_bonuses": {"PE": 2},
        "natural_weapons": [{"name": "Bite (1D6)", "cost": 5, "details": "Bite: 1D6"}],
        "abilities": [
            {"name": "Natural Armor: Light (AR 8, +20 SDC)", "cost": 5, "details": "AR 8; +20 SDC."},
            {"name": "Natural Armor: Medium (AR 10, +40 SDC)", "cost": 15, "details": "AR 10; +40 SDC."},
            {"name": "Natural Armor: Heavy (AR 12, +60 SDC)", "cost": 25, "details": "AR 12; +60 SDC."},
            {"name": "Natural Armor: Tough (AR 14, +80 SDC)", "cost": 35, "details": "AR 14; +80 SDC."},
            {"name": "Hold Breath", "cost": 5, "details": "Hold breath for extended periods."},
            {"name": "Master Swimmer", "cost": 5, "details": "Swimming skill or +20%; survives to 500 ft."},
        ],
    },

    "TURTLES — SNAPPING TURTLE": {
        "bio_e": 50,
        "original": {"size_level": 8, "length_in": 40, "weight_lbs": 200, "build": "Medium"},
        "mutant_changes_text": "Snapping turtle; uses same turtle armor block as pond turtle.",
        "attribute_bonuses": {"PS": 2},
        "natural_weapons": [
            {"name": "Claws (1D8)", "cost": 5, "details": "Claws: 1D8"},
            {"name": "Bite (1D6)", "cost": 5, "details": "Bite: 1D6"},
            {"name": "Bite (1D10)", "cost": 10, "details": "Bite: 1D10"},
        ],
        "abilities": [
            {"name": "Natural Armor: Light (AR 8, +20 SDC)", "cost": 5, "details": "AR 8; +20 SDC."},
            {"name": "Natural Armor: Medium (AR 10, +40 SDC)", "cost": 15, "details": "AR 10; +40 SDC."},
            {"name": "Natural Armor: Heavy (AR 12, +60 SDC)", "cost": 25, "details": "AR 12; +60 SDC."},
            {"name": "Natural Armor: Tough (AR 14, +80 SDC)", "cost": 35, "details": "AR 14; +80 SDC."},
            {"name": "Digging", "cost": 5, "details": "Digging ability."},
            {"name": "Hold Breath", "cost": 5, "details": "Hold breath for extended periods."},
            {"name": "Master Swimmer", "cost": 5, "details": "Swimming skill or +20%; survives to 500 ft."},
        ],
    },

    "WEASEL": {
        "bio_e": 80,
        "original": {"size_level": 1, "length_in": 18, "weight_lbs": 1, "build": "Long"},
        "mutant_changes_text": "Fearless carnivore; narrow body fits small holes.",
        "attribute_bonuses": {"ME": 2, "PS": 2, "PP": 3, "Spd": 5},
        "natural_weapons": [
            {"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Teeth (damage unclear)", "cost": 5, "details": "Bite damage not clearly stated in source line."},
        ],
        "abilities": [
            {"name": "Tight Squeeze (automatic)", "cost": 0, "details": "Can fit through very small openings."},
            {"name": "Hyper Metabolism", "cost": 20, "details": "+2 Initiative, +2 Dodge, +1 action/round, +10% Escape Artist; requires frequent naps/constant eating; must eat own weight daily; half meat."},
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Digging", "cost": 10, "details": "Digging ability."},
            {"name": "Tunneling", "cost": 20, "details": "Tunneling ability."},
            {"name": "Excavating", "cost": 30, "details": "Excavating ability."},
            {"name": "Nightvision", "cost": 10, "details": "See in darkness/low light."},
            {"name": "Advanced Smell", "cost": 10, "details": "Enhanced smell."},
        ],
    },

    "FERRET": {
        "bio_e": 80,
        "original": {"size_level": 1, "length_in": 18, "weight_lbs": 1, "build": "Long"},
        "mutant_changes_text": "Similar to weasels but friendlier; popular pets. Uses same ability package as Weasel per source note.",
        "attribute_bonuses": {"MA": 2, "PS": 2, "PP": 3, "Spd": 5},
        "natural_weapons": [
            {"name": "Claws (1D6) (climbing)", "cost": 5, "details": "Claws: 1D6; climbing."},
            {"name": "Teeth (damage unclear)", "cost": 5, "details": "Bite damage unclear in source line."},
        ],
        "abilities": [
            {"name": "Tight Squeeze (automatic)", "cost": 0, "details": "Can fit through very small openings."},
            {"name": "Hyper Metabolism", "cost": 20, "details": "+2 Initiative, +2 Dodge, +1 action/round, +10% Escape Artist; requires frequent naps/constant eating; must eat own weight daily; half meat."},
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Digging", "cost": 10, "details": "Digging ability."},
            {"name": "Tunneling", "cost": 20, "details": "Tunneling ability."},
            {"name": "Excavating", "cost": 30, "details": "Excavating ability."},
            {"name": "Nightvision", "cost": 10, "details": "See in darkness/low light."},
            {"name": "Advanced Smell", "cost": 10, "details": "Enhanced smell."},
        ],
    },

    "WOLVERINE": {
        "bio_e": 60,
        "original": {"size_level": 5, "length_in": 40, "weight_lbs": 30, "build": "Short"},
        "mutant_changes_text": "Northern carnivore with extreme endurance; can drive off bears; adaptable predator. Human-feature cost lines garbled in source.",
        "attribute_bonuses": {"IQ": 2, "ME": 2, "PS": 2, "PE": 4},
        "natural_weapons": [
            {"name": "Claws (1D8) (climbing)", "cost": 5, "details": "Claws: 1D8; climbing."},
            {"name": "Claws (1D12) (climbing)", "cost": 10, "details": "Claws: 1D12; climbing."},
            {"name": "Teeth (1D10)", "cost": 5, "details": "Bite: 1D10"},
        ],
        "abilities": [
            {"name": "Tough Hide (automatic)", "cost": 0, "details": "+20 SDC; +4 save vs cold; cold does half damage."},
            {"name": "Leaping", "cost": 5, "details": "Double Jump distance."},
            {"name": "Nightvision", "cost": 10, "details": "See in darkness/low light."},
            {"name": "Digging", "cost": 10, "details": "Digging ability."},
            {"name": "Advanced Smell", "cost": 10, "details": "Enhanced smell."},
        ],
    },
}

# ---------------- Bio-E helpers / defaults ----------------

def _bioe_norm(s: str) -> str:
    """Normalize an animal name for alias matching."""
    s = (s or "").strip().upper()
    s = s.replace("&", "AND")
    s = re.sub(r"[—–-]", " ", s)          # dashes to spaces
    s = re.sub(r"[^A-Z0-9 ]+", "", s)     # drop punctuation
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Default "empty" animal rule used when we can't resolve a selection.
BIOE_DEFAULT_ANIMAL: dict[str, Any] = {
    "bio_e": 0,
    "original": {"size_level": None, "length_in": None, "weight_lbs": None, "build": "Medium"},
    "mutant_changes_text": "",
    "attribute_bonuses": {},
    "natural_weapons": [],
    "abilities": [],
}


def _build_bioe_aliases(data: dict[str, dict[str, Any]]) -> dict[str, str]:
    """
    Builds a best-effort alias table so UI selections like "Dog", "Alligator",
    "Wild Turkey", etc. can map into BIOE_ANIMAL_DATA keys.
    """
    aliases: dict[str, str] = {}

    # 1) exact normalized keys for every BIOE_ANIMAL_DATA key
    for k in data.keys():
        aliases[_bioe_norm(k)] = k

    # 2) common UI-friendly names -> your data keys (add more anytime)
    manual = {
        # common TMNT tables / UI names
        "DOG": "CANINES — DOGS",
        "DOGS": "CANINES — DOGS",
        "CAT": "FELINES — CAT",
        "CROW": "BIRDS — CROW / RAVEN",
        "RAVEN": "BIRDS — CROW / RAVEN",
        "PIGEON": "BIRDS — PIGEON",
        "DOVE": "BIRDS — DOVE",
        "PARROT": "BIRDS — PARROT",
        "SONGBIRD": "BIRDS — TEMPERATE SONGBIRDS",
        "WILD SONGBIRD": "BIRDS — TEMPERATE SONGBIRDS",
        "SMALL WILD BIRD": "BIRDS — SMALL WILD BIRDS",
        "WILD GAME BIRD": "BIRDS — WILD GAME BIRDS (GROUSE / PARTRIDGE / PHEASANT / QUAIL)",
        "TURKEY": "BIRDS — TURKEY",
        "WILD TURKEY": "BIRDS — TURKEY",

        "FROG": "AMPHIBIANS — FROG & TOAD",
        "TOAD": "AMPHIBIANS — FROG & TOAD",
        "SALAMANDER": "AMPHIBIANS — SALAMANDER, NEWT, & AXOLOTL",
        "NEWT": "AMPHIBIANS — SALAMANDER, NEWT, & AXOLOTL",
        "AXOLOTL": "AMPHIBIANS — SALAMANDER, NEWT, & AXOLOTL",

        "TURTLE": "TURTLES — POND TURTLE",
        "SNAPPING TURTLE": "TURTLES — SNAPPING TURTLE",

        "ALLIGATOR": "ALLIGATOR & CROCODILE",
        "CROCODILE": "ALLIGATOR & CROCODILE",

        "BLACK BEAR": "BEAR — BLACK BEAR",
        "GRIZZLY BEAR": "BEAR — GRIZZLY",
        "KODIAK": "BEAR — BROWN (KODIAK)",
        "BROWN BEAR": "BEAR — BROWN (KODIAK)",
        "POLAR BEAR": "BEAR — POLAR",

        "BOBCAT": "FELINES — BOBCAT",
        "LYNX": "FELINES — LYNX",
        "COUGAR": "FELINES — COUGAR",
        "CHEETAH": "FELINES — CHEETAH",
        "LION": "FELINES — LION",
        "TIGER": "FELINES — TIGER",
        "LEOPARD": "FELINES — JAGUAR / LEOPARD",
        "JAGUAR": "FELINES — JAGUAR / LEOPARD",

        "FOX": "CANINES — FOX",
        "COYOTE": "CANINES — COYOTE",
        "WOLF": "CANINES — WOLF",

        "PIG": "PIG",
        "BOAR": "BOAR",
        "RACCOON": "RACCOON",
        "SKUNK": "SKUNK (Striped)",
        "PORCUPINE": "PORCUPINE",
        "SQUIRREL": "SQUIRREL",
        "BEAVER": "BEAVER",
        "MUSKRAT": "MUSKRAT",
        "MOLE": "MOLE",
        "WEASEL": "WEASEL",
        "FERRET": "FERRET",
        "WOLVERINE": "WOLVERINE",
        "BADGER": "BADGER",
        "ARMADILLO": "ARMADILLO",
        "AARDVARK": "AARDVARK",
        "ELEPHANT": "ELEPHANT",
        "RHINOCEROS": "RHINOCEROS",
        "HIPPOPOTAMUS": "HIPPOPOTAMUS",
        "CAMEL": "CAMEL",
        "BISON": "BUFFALO & BISON",
        "BUFFALO": "BUFFALO & BISON",
        "CHIMPANZEE": "APES — CHIMPANZEE",
        "GORILLA": "APES — GORILLA",
        "ORANGUTAN": "APES — ORANGUTAN",
        "MONKEY": "MONKEY (ARBOREAL)",
        "BABOON": "BABOON",

        # group-ish
        "LIZARD": "LIZARDS (GROUP ENTRY)",
        "LIZARDS": "LIZARDS (GROUP ENTRY)",
        "RODENT": "RODENTS (GROUP ENTRY)",
        "RODENTS": "RODENTS (GROUP ENTRY)",
        "SHARK": "SHARK (Tiger Shark baseline)",
        "BAT": "BAT",
    }

    for k, v in manual.items():
        if v in data:
            aliases[_bioe_norm(k)] = v

    return aliases


BIOE_ANIMAL_ALIASES: dict[str, str] = _build_bioe_aliases(BIOE_ANIMAL_DATA)





GEAR_BY_NAME = {g["name"]: g for g in GEAR_CATALOG}

# ---------------- TMNT & Other Strangeness: Determine the Animal tables ----------------
TMNTOS_ANIMAL_TYPE_RANGES: list[tuple[range, str]] = [
    (range(1, 26), "Urban Animals"),
    (range(26, 41), "Rural Animals"),
    (range(41, 66), "Wild Animals"),
    (range(66, 76), "Wild Birds"),
    (range(76, 91), "Zoo Animals"),
    (range(91, 101), "Lab Animals"),
]

TMNTOS_ANIMALS_BY_TYPE: dict[str, list[tuple[range, str]]] = {
    "Urban Animals": [
        (range(1, 26), "Dog"),
        (range(26, 46), "Cat"),
        (range(46, 51), "Newt"),
        (range(51, 56), "Crow"),
        (range(56, 61), "Pet Rodent (Gerbil, Hamster, etc.)"),
        (range(61, 66), "Squirrel"),
        (range(66, 76), "Pet Ferret"),
        (range(76, 84), "Pigeon"),
        (range(84, 89), "Bird (Songbird or Parrot)"),
        (range(89, 93), "Bat"),
        (range(93, 95), "Turtle"),
        (range(95, 97), "Frog"),
        (range(97, 101), "Lizard"),
    ],
    "Rural Animals": [
        (range(1, 6), "Dog"),
        (range(6, 11), "Cat"),
        (range(11, 16), "Cow or Bull"),
        (range(16, 21), "Pig"),
        (range(21, 31), "Chicken"),
        (range(31, 36), "Duck"),
        (range(36, 51), "Horse"),
        (range(51, 61), "Rabbit"),
        (range(61, 66), "Rat"),
        (range(66, 71), "Sheep"),
        (range(71, 81), "Goat"),
        (range(81, 86), "Turkey"),
        (range(86, 89), "Bat"),
        (range(89, 95), "Raccoon"),
        (range(95, 99), "Frog"),
        (range(99, 101), "Salamander"),
    ],
    "Wild Animals": [
        (range(1, 6), "Wolf"),
        (range(6, 11), "Coyote"),
        (range(11, 16), "Fox"),
        (range(16, 21), "Badger"),
        (range(21, 26), "Black Bear"),
        (range(26, 28), "Grizzly Bear"),
        (range(28, 31), "Cougar"),
        (range(31, 34), "Bobcat"),
        (range(34, 36), "Lynx"),
        (range(36, 38), "Wolverine"),
        (range(38, 46), "Weasel"),
        (range(46, 50), "Alligator"),
        (range(50, 53), "Otter"),
        (range(53, 56), "Beaver"),
        (range(56, 61), "Muskrat"),
        (range(61, 66), "Raccoon"),
        (range(66, 71), "Boar"),
        (range(71, 76), "Skunk"),
        (range(76, 81), "Porcupine"),
        (range(81, 84), "Opossum"),
        (range(84, 86), "Marten"),
        (range(86, 89), "Armadillo"),
        (range(89, 96), "Deer"),
        (range(96, 98), "Elk"),
        (range(98, 100), "Moose"),
        (range(100, 101), "Mole"),
    ],
    "Wild Birds": [
        (range(1, 6), "Duck"),
        (range(6, 11), "Goose"),
        (range(11, 16), "Swan"),
        (range(16, 21), "Cardinal"),
        (range(21, 31), "Wild Turkey"),
        (range(31, 36), "Small Wild Bird"),
        (range(36, 51), "Wild Game Bird"),
        (range(51, 61), "Raven"),
        (range(61, 66), "Pigeon"),
        (range(66, 71), "Wild Songbird"),
        (range(71, 81), "Hawk"),
        (range(81, 86), "Falcon"),
        (range(86, 91), "Eagle"),
        (range(91, 96), "Owl"),
        (range(96, 99), "Escaped Pet Songbird"),
        (range(99, 101), "Escaped Pet Parrot"),
    ],
    "Zoo Animals": [
        (range(1, 5), "Lion"),
        (range(5, 9), "Tiger"),
        (range(9, 13), "Leopard"),
        (range(13, 17), "Cheetah"),
        (range(17, 21), "Polar Bear"),
        (range(21, 25), "Crocodile (or Alligator)"),
        (range(25, 29), "Aardvark"),
        (range(29, 33), "Rhinoceros"),
        (range(33, 37), "Hippopotamus"),
        (range(37, 41), "Elephant"),
        (range(41, 45), "Chimpanzee"),
        (range(45, 49), "Orangutan"),
        (range(49, 53), "Gorilla"),
        (range(53, 57), "Monkey"),
        (range(57, 61), "Baboon"),
        (range(61, 65), "Camel"),
        (range(65, 69), "Bison (or Buffalo)"),
        (range(69, 73), "Lemur"),
        (range(73, 77), "Shark"),
        (range(77, 81), "Octopus"),
        (range(81, 85), "Squid"),
        (range(85, 89), "Penguin"),
        (range(89, 93), "Kodiak (Brown Bear)"),
        (range(93, 97), "Lizard"),
        (range(97, 101), "Komodo Dragon"),
    ],
    "Lab Animals": [
        (range(1, 26), "Mouse"),
        (range(26, 46), "Rat"),
        (range(46, 51), "Songbird"),
        (range(51, 56), "Dog"),
        (range(56, 61), "Cat"),
        (range(61, 66), "Rabbit"),
        (range(66, 76), "Guinea Pig"),
        (range(76, 81), "Hamster"),
        (range(81, 86), "Chimpanzee"),
        (range(86, 90), "Monkey"),
        (range(90, 94), "Pig"),
        (range(94, 98), "Sheep"),
        (range(98, 101), "Salamander"),
    ],
}


def _unique_items(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


# ---- Size tables ----
SIZE_LEVEL_EFFECTS: dict[int, dict[str, int]] = {
    1: {"bio_e": 0, "IQ": -8, "PS": -12, "PE": -4, "Speed": +7, "SDC": 5},
    2: {"bio_e": 5, "IQ": -6, "PS": -6, "PE": -2, "Speed": +5, "SDC": 10},
    3: {"bio_e": 10, "IQ": -4, "PS": -3, "PE": -1, "Speed": +3, "SDC": 15},
    4: {"bio_e": 15, "IQ": -2, "PS": -2, "PE": 0, "Speed": 0, "SDC": 20},
    5: {"bio_e": 20, "IQ": 0, "PS": -1, "PE": 0, "Speed": 0, "SDC": 25},
    6: {"bio_e": 25, "IQ": 0, "PS": 0, "PE": 0, "Speed": 0, "SDC": 30},
    7: {"bio_e": 30, "IQ": 0, "PS": +1, "PE": 0, "Speed": 0, "SDC": 30},
    8: {"bio_e": 35, "IQ": 0, "PS": +2, "PE": 0, "Speed": 0, "SDC": 35},
    9: {"bio_e": 40, "IQ": 0, "PS": +3, "PE": +1, "Speed": 0, "SDC": 35},
    10: {"bio_e": 45, "IQ": 0, "PS": +4, "PE": +2, "Speed": 0, "SDC": 35},
    11: {"bio_e": 50, "IQ": 0, "PS": +5, "PE": +3, "Speed": -1, "SDC": 40},
    12: {"bio_e": 55, "IQ": 0, "PS": +6, "PE": +4, "Speed": -2, "SDC": 40},
    13: {"bio_e": 60, "IQ": 0, "PS": +7, "PE": +5, "Speed": -3, "SDC": 45},
    14: {"bio_e": 65, "IQ": 0, "PS": +8, "PE": +6, "Speed": -4, "SDC": 50},
    15: {"bio_e": 70, "IQ": 0, "PS": +9, "PE": +7, "Speed": -5, "SDC": 55},
    16: {"bio_e": 75, "IQ": 0, "PS": +10, "PE": +8, "Speed": -6, "SDC": 60},
    17: {"bio_e": 80, "IQ": 0, "PS": +11, "PE": +9, "Speed": -7, "SDC": 65},
    18: {"bio_e": 85, "IQ": 0, "PS": +12, "PE": +10, "Speed": -8, "SDC": 70},
    19: {"bio_e": 90, "IQ": 0, "PS": +13, "PE": +11, "Speed": -9, "SDC": 75},
    20: {"bio_e": 95, "IQ": 0, "PS": +14, "PE": +12, "Speed": -10, "SDC": 80},
}

SIZE_LEVEL_FORMULAS: dict[int, dict[str, str]] = {
    1: {"weight": "3D6 ounces", "short": "1D6 inches", "medium": "2D6 inches", "long": "3D6 inches"},
    2: {"weight": "1D6 lbs", "short": "3D6 inches", "medium": "12+2D6 inches", "long": "12+2D6 inches"},
    3: {"weight": "4+1D6 lbs", "short": "12+1D6 inches", "medium": "12+3D6 inches", "long": "12+3D6 inches"},
    4: {"weight": "10+2D6 lbs", "short": "12+3D6 inches", "medium": "24+2D6 inches", "long": "24+3D6 inches"},
    5: {"weight": "20+4D6 lbs", "short": "24+1D6 inches", "medium": "36+1D6 inches", "long": "36+3D6 inches"},
    6: {"weight": "40+6D6 lbs", "short": "24+2D6 inches", "medium": "36+2D6 inches", "long": "48+3D6 inches"},
    7: {"weight": "75+3D10 lbs", "short": "24+3D6 inches", "medium": "48+1D6 inches", "long": "60+2D6 inches"},
    8: {"weight": "100+6D10 lbs", "short": "36+1D6 inches", "medium": "48+2D6 inches", "long": "60+3D6 inches"},
    9: {"weight": "150+3D10 lbs", "short": "36+2D6 inches", "medium": "60+1D6 inches", "long": "72+2D6 inches"},
    10: {"weight": "175+3D10 lbs", "short": "36+3D6 inches", "medium": "60+3D6 inches", "long": "72+2D6 inches"},
    11: {"weight": "200+6D10 lbs", "short": "48+1D6 inches", "medium": "72+1D6 inches", "long": "84+3D6 inches"},
    12: {"weight": "250+6D10 lbs", "short": "48+2D6 inches", "medium": "72+2D6 inches", "long": "84+3D6 inches"},
    13: {"weight": "300+6D10 lbs", "short": "48+3D6 inches", "medium": "72+2D6 inches", "long": "96+3D6 inches"},
    14: {"weight": "350+6D10 lbs", "short": "60+1D6 inches", "medium": "84+1D6 inches", "long": "96+3D6 inches"},
    15: {"weight": "400+1D% lbs", "short": "60+2D6 inches", "medium": "84+2D6 inches", "long": "108+3D6 inches"},
    16: {"weight": "500+1D% lbs", "short": "60+3D6 inches", "medium": "84+3D6 inches", "long": "108+3D6 inches"},
    17: {"weight": "600+2D% lbs", "short": "72+1D6 inches", "medium": "96+1D6 inches", "long": "120+2D6 inches"},
    18: {"weight": "800+2D% lbs", "short": "72+2D6 inches", "medium": "96+2D6 inches", "long": "120+3D6 inches"},
    19: {"weight": "1,000+5D% lbs", "short": "72+3D6 inches", "medium": "96+2D6 inches", "long": "132+2D6 inches"},
    20: {"weight": "1,500 + (1D% x 100) lbs", "short": "72+4D6 inches", "medium": "108+1D6 inches", "long": "132+3D6 inches"},
}

# ---------------- Combat Training Rules ----------------
BASELINE_COMBAT: dict[str, Any] = {
    "actions_per_round": 2,
    "unarmed_damage": "1D4",
    "known_actions": ["Attack", "Disarm", "Tackle"],
    "known_reactions": ["Parry", "Dodge", "Roll with Impact"],
    "critical_range": (20, 20),
    "notes": [
        "Combat Training bonuses are cumulative (they stack as you level).",
        "Critical Strike on a natural 20 doubles damage (baseline).",
    ],
}

COMBAT_TRAINING_RULES: dict[str, dict[int, dict[str, Any]]] = {
    "Basic Combat Training": {
        1: {"unlock_reactions": ["Automatic Parry"], "roll_with_impact": 1},
        2: {"parry": 1, "dodge": 1},
        3: {"strike": 1},
        4: {"actions_per_round": 1},
        5: {"unlock_reactions": ["Entangle"]},
        6: {"melee_damage": "+1", "initiative": 1},
        7: {"critical_range": (19, 20)},
        8: {"unlock_actions": ["Throw"]},
        9: {"actions_per_round": 1},
        10: {"roll_with_impact": 1},
        11: {"parry": 1, "dodge": 1, "strike": 1},
        12: {"unlock_actions": ["Hold"]},
        13: {"melee_damage": "+1", "initiative": 1},
        14: {"actions_per_round": 1},
        15: {"specials": ["Critical Strike or Stun with a melee Sneak Attack"]},
    },
    "Expert Combat Training": {
        1: {"unlock_reactions": ["Automatic Parry"], "roll_with_impact": 2},
        2: {"parry": 2, "dodge": 2, "strike": 2},
        3: {"unlock_reactions": ["Entangle"]},
        4: {"actions_per_round": 1},
        5: {"unlock_actions": ["Throw"]},
        6: {"melee_damage": "+2", "initiative": 2},
        7: {"critical_range": (18, 20)},
        8: {"unlock_actions": ["Hold"]},
        9: {"actions_per_round": 1},
        10: {"roll_with_impact": 2},
        11: {"parry": 2, "dodge": 2, "strike": 2},
        12: {"unlock_reactions": ["Disarm (reaction)"]},
        13: {"roll_with_impact": 2},
        14: {"actions_per_round": 1},
        15: {"specials": ["Death Blow with melee attacks on a natural 20"]},
    },
    "Martial Arts Combat Training": {
        1: {"unlock_reactions": ["Automatic Parry"], "roll_with_impact": 3},
        2: {"parry": 3, "dodge": 3, "strike": 3},
        3: {"unlock_reactions": ["Entangle"], "unlock_actions": ["Throw"]},
        4: {"actions_per_round": 1},
        5: {"melee_damage": "+3", "initiative": 3},
        6: {"unlock_actions": ["Hold"], "unlock_reactions": ["Disarm (reaction)"]},
        7: {"critical_range": (18, 20)},
        8: {"specials": ["Critical Strike or Stun with a melee Sneak Attack"]},
        9: {"actions_per_round": 1},
        10: {"unlock_actions": ["Leap Attack"], "unlock_reactions": ["Throw (reaction)"]},
        11: {"parry": 2, "dodge": 2, "strike": 2},
        12: {"roll_with_impact": 2},
        13: {"specials": ["Critical Strike or Stun with melee on a natural 18–20"]},
        14: {"actions_per_round": 1},
        15: {"specials": ["Death Blow with melee attacks on a natural 20"]},
    },
    "Ninjutsu Combat Training (Special)": {
        1: {"unlock_reactions": ["Automatic Parry"], "roll_with_impact": 4},
        2: {"parry": 3, "dodge": 3, "strike": 3},
        3: {"unlock_reactions": ["Entangle"], "unlock_actions": ["Throw"]},
        4: {"actions_per_round": 1, "unlock_actions": ["Leap Attack"]},
        5: {"specials": ["Critical Strike or Stun with a melee Sneak Attack"]},
        6: {"melee_damage": "+2", "initiative": 2},
        7: {"critical_range": (18, 20)},
        8: {"unlock_actions": ["Hold"], "unlock_reactions": ["Disarm (reaction)"]},
        9: {"actions_per_round": 1},
        10: {"unlock_reactions": ["Throw (reaction)"], "roll_with_impact": 2},
        11: {"parry": 2, "dodge": 2, "strike": 2},
        12: {"specials": ["Death Blow with melee attacks on a natural 20"]},
        13: {"melee_damage": "+3", "initiative": 3},
        14: {"actions_per_round": 1},
        15: {"specials": ["Critical Strike or Stun with melee on a natural 17–20"]},
    },
    "Assassin Combat Training (Special)": {
        1: {"unlock_reactions": ["Automatic Parry"], "roll_with_impact": 3},
        2: {"parry": 2, "dodge": 2, "strike": 2},
        3: {"specials": ["Critical Strike or Stun with a melee Sneak Attack"]},
        4: {"actions_per_round": 1},
        5: {"melee_damage": "+3", "initiative": 3},
        6: {"unlock_reactions": ["Entangle"], "unlock_actions": ["Throw"]},
        7: {"critical_range": (19, 20)},
        8: {"specials": ["Critical Strike or Stun with melee on a natural 17–20"]},
        9: {"actions_per_round": 1},
        10: {"specials": ["Death Blow with melee attacks on a natural 20"]},
        11: {"parry": 2, "dodge": 2, "strike": 2},
        12: {"roll_with_impact": 2},
        13: {"melee_damage": "+2", "initiative": 2},
        14: {"actions_per_round": 1},
        15: {"critical_range": (17, 20)},
    },
    "Feral Combat Training (Special)": {
        1: {"unlock_reactions": ["Automatic Parry"], "roll_with_impact": 2},
        2: {"strike": 3, "parry": 2, "dodge": 2},
        3: {"melee_damage": "+3", "initiative": 1},
        4: {"actions_per_round": 1},
        5: {"unlock_reactions": ["Entangle"], "unlock_actions": ["Throw"]},
        6: {"melee_damage": "+3", "initiative": 1},
        7: {"specials": ["Critical Strike or Stun with melee on a natural 17–20"]},
        8: {"strike": 3},
        9: {"actions_per_round": 1},
        10: {"unlock_actions": ["Leap Attack"]},
        11: {"parry": 2, "dodge": 2, "roll_with_impact": 1},
        12: {"specials": ["Critical Strike or Stun with a melee Sneak Attack"]},
        13: {"melee_damage": "+4", "initiative": 2},
        14: {"actions_per_round": 1},
        15: {"specials": ["Death Blow with melee attacks on a natural 20"]},
    },
}


def _training_names() -> list[str]:
    return ["None"] + sorted(COMBAT_TRAINING_RULES.keys())


def _combine_melee_damage(dmg_list: list[str]) -> str:
    if not dmg_list:
        return "—"
    return ", ".join(dmg_list)


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        logo_path = project_root() / "assets" / "images" / "TurtleCom Logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                logo = QLabel()
                logo.setAlignment(Qt.AlignHCenter)
                logo.setPixmap(pix.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                layout.addWidget(logo)

        title = QLabel(f"<h2>{APP_NAME} <span style='font-weight:400'>({APP_VERSION})</span></h2>")
        title.setAlignment(Qt.AlignHCenter)
        layout.addWidget(title)

        credits = QLabel(
            "Offline TMNT & Other Strangeness Redux character tool.<br>"
            "Built with Python + PySide6 (Qt).<br><br>"
            "<b>Credits</b><br>"
            "Design & implementation: Belor Mck + ChatGPT via VIBE CODING!<br>"
            "Rules/content: TMNT & Other Strangeness Redux (Palladium Books)<br>"
        )
        credits.setAlignment(Qt.AlignHCenter)
        credits.setWordWrap(True)
        layout.addWidget(credits)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    # ---------------- Bio-E lookup helpers ----------------

    BIOE_DEFAULT_ANIMAL: dict[str, Any] = {
        "bio_e": 0,
        "original": {"size_level": None, "length_in": None, "weight_lbs": None, "build": "Medium"},
        "mutant_changes_text": "",
        "attribute_bonuses": {},
        "natural_weapons": [],
        "abilities": [],
    }

    def _norm_animal_label(s: str) -> str:
        """Normalize UI labels like 'Black Bear' -> 'BLACK BEAR' for alias matching."""
        if not s:
            return ""
        s = s.strip().upper()

        # normalize punctuation / separators
        s = s.replace("—", "-").replace("–", "-")
        s = s.replace("&", " AND ")
        s = s.replace("/", " ")
        s = s.replace("(", " ").replace(")", " ")
        s = s.replace(",", " ")
        s = re.sub(r"\s+", " ", s).strip()
        return s

    # Map the UI animal names (TMNT tables / your combo labels) to BIOE_ANIMAL_DATA keys.
    # Add to this as you discover more label variants in your tables.
    BIOE_ANIMAL_ALIASES: dict[str, str] = {
        # --- Canines ---
        "DOG": "CANINES — DOGS",
        "DOGS": "CANINES — DOGS",
        "FOX": "CANINES — FOX",
        "COYOTE": "CANINES — COYOTE",
        "WOLF": "CANINES — WOLF",

        # --- Felines ---
        "CAT": "FELINES — CAT",
        "BOBCAT": "FELINES — BOBCAT",
        "LYNX": "FELINES — LYNX",
        "COUGAR": "FELINES — COUGAR",
        "CHEETAH": "FELINES — CHEETAH",
        "LION": "FELINES — LION",
        "TIGER": "FELINES — TIGER",
        "LEOPARD": "FELINES — JAGUAR / LEOPARD",
        "JAGUAR": "FELINES — JAGUAR / LEOPARD",

        # --- Bears ---
        "BLACK BEAR": "BEAR — BLACK BEAR",
        "GRIZZLY BEAR": "BEAR — GRIZZLY",
        "GRIZZLY": "BEAR — GRIZZLY",
        "BROWN BEAR": "BEAR — BROWN (KODIAK)",
        "KODIAK": "BEAR — BROWN (KODIAK)",
        "KODIAK BEAR": "BEAR — BROWN (KODIAK)",
        "POLAR BEAR": "BEAR — POLAR",

        # --- Reptiles / Amphibians ---
        "ALLIGATOR": "ALLIGATOR & CROCODILE",
        "CROCODILE": "ALLIGATOR & CROCODILE",
        "FROG": "AMPHIBIANS — FROG & TOAD",
        "TOAD": "AMPHIBIANS — FROG & TOAD",
        "SALAMANDER": "AMPHIBIANS — SALAMANDER, NEWT, & AXOLOTL",
        "NEWT": "AMPHIBIANS — SALAMANDER, NEWT, & AXOLOTL",
        "AXOLOTL": "AMPHIBIANS — SALAMANDER, NEWT, & AXOLOTL",
        "TURTLE": "TURTLES — POND TURTLE",
        "POND TURTLE": "TURTLES — POND TURTLE",
        "SNAPPING TURTLE": "TURTLES — SNAPPING TURTLE",

        # --- Farm / common ---
        "COW": "CATTLE — COW",
        "BULL": "CATTLE — BULL",
        "PIG": "PIG",
        "BOAR": "BOAR",
        "GOAT": "GOAT",
        "HORSE": "HORSE (RIDING HORSE)",
        "RIDING HORSE": "HORSE (RIDING HORSE)",
        "RABBIT": "RABBIT",

        # --- Birds (TMNT tables often use generic names) ---
        "CHICKEN": "BIRDS — CHICKEN",
        "DUCK": "BIRDS — DUCK",
        "GOOSE": "BIRDS — GOOSE",
        "SWAN": "BIRDS — SWAN",
        "PIGEON": "BIRDS — PIGEON",
        "DOVE": "BIRDS — DOVE",
        "PARROT": "BIRDS — PARROT",
        "CROW": "BIRDS — CROW / RAVEN",
        "RAVEN": "BIRDS — CROW / RAVEN",
        "HAWK": "BIRDS — HAWK / FALCON",
        "FALCON": "BIRDS — HAWK / FALCON",
        "EAGLE": "BIRDS — EAGLE",
        "PENGUIN": "BIRDS — PENGUIN",
        "TURKEY": "BIRDS — TURKEY",
        "WILD TURKEY": "BIRDS — TURKEY",
        "SMALL WILD BIRD": "BIRDS — SMALL WILD BIRDS",
        "WILD SONGBIRD": "BIRDS — TEMPERATE SONGBIRDS",
        "SONGBIRD": "BIRDS — TEMPERATE SONGBIRDS",

        # --- Other common TMNT table animals ---
        "RACCOON": "RACCOON",
        "SKUNK": "SKUNK (Striped)",
        "PORCUPINE": "PORCUPINE",
        "ARMADILLO": "ARMADILLO",
        "BADGER": "BADGER",
        "BEAVER": "BEAVER",
        "MUSKRAT": "MUSKRAT",
        "MARTEN": "MARTEN & MINK",
        "MINK": "MARTEN & MINK",
        "WEASEL": "WEASEL",
        "FERRET": "FERRET",
        "WOLVERINE": "WOLVERINE",
        "DEER": "DEER",
        "ELK": "ELK",
        "MOOSE": "MOOSE",
        "ELEPHANT": "ELEPHANT",
        "RHINOCEROS": "RHINOCEROS",
        "HIPPOPOTAMUS": "HIPPOPOTAMUS",
        "CAMEL": "CAMEL",
        "BISON": "BUFFALO & BISON",
        "BUFFALO": "BUFFALO & BISON",
        "LEMUR": "LEMUR",
        "BAT": "BAT",

        # --- Groups / placeholders (if your tables roll these generically) ---
        "LIZARD": "LIZARDS (GROUP ENTRY)",
        "LIZARDS": "LIZARDS (GROUP ENTRY)",
        "RODENT": "RODENTS (GROUP ENTRY)",
        "RAT": "RODENTS (GROUP ENTRY)",
        "MOUSE": "RODENTS (GROUP ENTRY)",
        "GUINEA PIG": "RODENTS (GROUP ENTRY)",
        "HAMSTER": "RODENTS (GROUP ENTRY)",
        "GERBIL": "RODENTS (GROUP ENTRY)",
    }


    # ---------------- Bio-E lookup helpers (MODULE LEVEL) ----------------

    BIOE_DEFAULT_ANIMAL: dict[str, Any] = {
        "bio_e": 0,
        "original": {"size_level": None, "length_in": None, "weight_lbs": None, "build": "Medium"},
        "mutant_changes_text": "",
        "attribute_bonuses": {},
        "natural_weapons": [],
        "abilities": [],
    }

    PHYSICAL_SKILL_EFFECTS: dict[str, dict[str, Any]] = {
        "Acrobatics": {
            "attribute_bonus": {"PP": 1, "PE": 1},
            "combat_bonus": {"roll_with_impact": 2},
            "sdc_roll": "1d6",
            "skill_bonus_pct": {"Prowl": 5, "Climbing": 5},
            "extra_attacks": [],
            "notes": [
                "Balancing / Walk Tightrope / Highwire 50% +5% per level",
                "Jumping / Flip / Tumble 50% +5% per level",
                "Can jump further than normal",
            ],
        },
        "General Athletics": {
            "attribute_bonus": {"PS": 1, "PE": 1},
            "combat_bonus": {"parry": 1, "dodge": 1, "roll_with_impact": 1},
            "speed_roll": "1d6",
            "sdc_roll": "1d10",
            "extra_attacks": [],
            "notes": [],
        },
        "Body Building": {
            "attribute_rolls": {"PS": "1d4+1"},
            "combat_bonus": {},
            "sdc_flat": 10,
            "extra_attacks": [],
            "notes": [],
        },
        "Boxing": {
            "attribute_bonus": {"PS": 1, "PE": 1},
            "combat_bonus": {"parry": 1, "dodge": 1, "actions_per_round": 1, "pull_punch": 1},
            "sdc_roll": "1d12",
            "extra_attacks": [],
            "notes": [
                "Critical Strike with unarmed melee automatically stuns opponent for 1d4 rounds.",
            ],
        },
        "Climbing": {
            "attribute_bonus": {"PS": 1, "PE": 1},
            "combat_bonus": {},
            "sdc_roll": "1d6",
            "skill_bonus_pct": {},
            "extra_attacks": [],
            "notes": [
                "Second roll to recover hold after failed climb.",
                "Rappelling included for game purposes.",
            ],
        },
        "Fencing": {
            "attribute_bonus": {},
            "combat_bonus": {"strike_swords": 1, "parry_swords": 1, "damage_swords": 2},
            "extra_attacks": [],
            "notes": [
                "Bonuses stack with WP Sword and Combat Training.",
            ],
        },
        "Gymnastics": {
            "attribute_bonus": {"PS": 1, "PP": 1},
            "combat_bonus": {"roll_with_impact": 2},
            "sdc_roll": "1d8",
            "skill_bonus_pct": {"Prowl": 5, "Climbing": 5},
            "extra_attacks": [],
            "notes": [
                "Balancing / Jumping 40% +5% per level",
                "Flip / Tumble 60% +5% per level",
                "Can jump further than normal",
            ],
        },
        "Prowl": {
            "attribute_bonus": {},
            "combat_bonus": {},
            "extra_attacks": ["Sneak Attack"],
            "notes": [
                "Successful prowl may enable Sneak Attack.",
            ],
        },
        "Running": {
            "attribute_bonus": {"PE": 2},
            "combat_bonus": {},
            "speed_roll": "4d4",
            "sdc_roll": "1d6",
            "extra_attacks": [],
            "notes": [],
        },
        "Swimming": {
            "attribute_bonus": {},
            "combat_bonus": {},
            "extra_attacks": [],
            "notes": [],
        },
        "Advanced Swimming": {
            "attribute_bonus": {"PS": 1, "PE": 1},
            "combat_bonus": {},
            "sdc_roll": "1d6",
            "swim_speed_roll": "3d4",
            "extra_attacks": [],
            "notes": [],
        },
        "Wrestling": {
            "attribute_bonus": {"PS": 1, "PE": 1},
            "combat_bonus": {"roll_with_impact": 1, "pull_punch": 1},
            "sdc_roll": "1d12",
            "extra_attacks": ["Throw Attack", "Crush Attack", "Hold on Critical"],
            "notes": [
                "Throw Attack deals +2 damage.",
                "Crush Attack deals +4 unarmed damage to held target; target cannot Parry or Dodge.",
                "Critical Strike with unarmed melee automatically gets a Hold.",
            ],
        },
    }



class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Character Generator ({APP_VERSION})")
        self.resize(1100, 700)

        self.current_path: Optional[Path] = None
        self.current_character: Character = Character()

        self.dark_mode_enabled: bool = True

        self.skill_rules: dict[str, Any] = {}
        self.pro_skill_lookup: dict[str, dict[str, Any]] = {}
        self.amateur_skill_lookup: dict[str, dict[str, Any]] = {}
        self.pro_model: Optional[QStandardItemModel] = None
        self.amateur_model: Optional[QStandardItemModel] = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.welcome_page = QWidget()
        self.editor_page = QWidget()

        self.stack.addWidget(self.welcome_page)
        self.stack.addWidget(self.editor_page)

        self._build_menu()
        self._build_toolbar()

        self._build_welcome_page()
        self._build_editor_page()

        self.statusBar().showMessage("Ready")
        self.version_label = QLabel(APP_VERSION)
        self.statusBar().addPermanentWidget(self.version_label)

        self.refresh_list()
        self.refresh_welcome_list()
        self.on_toggle_dark_mode(True)

        self.stack.setCurrentWidget(self.welcome_page)


    # ----------- Scroll Bars --------
    def make_scrollable_tab(self, tab_widget: QWidget) -> QVBoxLayout:
        outer = QVBoxLayout(tab_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        inner = QWidget()
        scroll.setWidget(inner)

        layout = QVBoxLayout(inner)
        return layout

    # ---------------- Menu / Toolbar ----------------
    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")

        self.action_new = QAction("&New", self)
        self.action_new.setShortcut("Ctrl+N")
        self.action_new.triggered.connect(self.on_new)
        file_menu.addAction(self.action_new)

        self.action_load = QAction("&Load...", self)
        self.action_load.setShortcut("Ctrl+O")
        self.action_load.triggered.connect(self.on_load_dialog)
        file_menu.addAction(self.action_load)

        file_menu.addSeparator()

        self.action_save = QAction("&Save", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.triggered.connect(self.on_save)
        file_menu.addAction(self.action_save)

        self.action_save_as = QAction("Save &As...", self)
        self.action_save_as.setShortcut("Ctrl+Shift+S")
        self.action_save_as.triggered.connect(self.on_save_as)
        file_menu.addAction(self.action_save_as)

        file_menu.addSeparator()

        self.action_delete = QAction("&Delete", self)
        self.action_delete.triggered.connect(self.on_delete)
        file_menu.addAction(self.action_delete)

        file_menu.addSeparator()

        self.action_back_to_start = QAction("Back to Start Screen", self)
        self.action_back_to_start.triggered.connect(self.go_to_start_screen)
        file_menu.addAction(self.action_back_to_start)

        file_menu.addSeparator()

        self.action_exit = QAction("E&xit", self)
        self.action_exit.setShortcut("Alt+F4")
        self.action_exit.triggered.connect(self.close)
        file_menu.addAction(self.action_exit)

        settings_menu = menubar.addMenu("&Settings")

        self.action_dark_mode = QAction("Enable &Dark Mode", self)
        self.action_dark_mode.setCheckable(True)
        self.action_dark_mode.setChecked(True)
        self.action_dark_mode.toggled.connect(self.on_toggle_dark_mode)
        settings_menu.addAction(self.action_dark_mode)

        help_menu = menubar.addMenu("&Help")

        self.action_about = QAction("&About TurtleCom", self)
        self.action_about.triggered.connect(self.show_about)
        help_menu.addAction(self.action_about)

    def _build_toolbar(self) -> None:
        tb = QToolBar("Main", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        tb.addAction(self.action_new)
        tb.addAction(self.action_load)
        tb.addAction(self.action_save)
        tb.addSeparator()
        tb.addAction(self.action_back_to_start)

    def show_about(self) -> None:
        dlg = AboutDialog(self)
        dlg.exec()


    def _build_welcome_page(self) -> None:
        layout = QVBoxLayout(self.welcome_page)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        layout.setSpacing(14)

        title = QLabel(
            "<h2 style='margin:0;'>TURTLE COM - A Teenage Mutant Ninja Turtle &amp; Other Strangeness generator.</h2>"
        )
        title.setAlignment(Qt.AlignHCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        logo_path = project_root() / "assets" / "images" / "TurtleCom Logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                logo = QLabel()
                logo.setAlignment(Qt.AlignHCenter)
                logo.setPixmap(pix.scaled(260, 260, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                layout.addWidget(logo)

        btn_row = QHBoxLayout()

        self.btn_welcome_new = QPushButton("Create new character")
        self.btn_welcome_new.clicked.connect(self.on_welcome_new)
        btn_row.addWidget(self.btn_welcome_new)

        self.btn_welcome_random = QPushButton("Generate random level 1 character")
        self.btn_welcome_random.clicked.connect(self.on_welcome_random_level1)
        btn_row.addWidget(self.btn_welcome_random)

        layout.addLayout(btn_row)

        saved_box = QGroupBox("Saved Characters")
        saved_layout = QVBoxLayout(saved_box)

        self.welcome_list = QListWidget()
        self.welcome_list.itemDoubleClicked.connect(self.on_welcome_load_selected)
        saved_layout.addWidget(self.welcome_list, 1)

        load_row = QHBoxLayout()

        self.btn_welcome_load_selected = QPushButton("Load selected character")
        self.btn_welcome_load_selected.clicked.connect(self.on_welcome_load_selected)
        load_row.addWidget(self.btn_welcome_load_selected)

        self.btn_welcome_browse = QPushButton("Browse…")
        self.btn_welcome_browse.clicked.connect(self.on_welcome_browse_load)
        load_row.addWidget(self.btn_welcome_browse)

        saved_layout.addLayout(load_row)
        layout.addWidget(saved_box)

    # ---------------- Random Level 1 (implemented) ----------------
    def on_welcome_random_level1(self) -> None:
        self._enter_editor()
        self.load_into_editor(Character(), None)
        self.generate_random_level1_character()
    
    def generate_random_level1_character(self) -> None:
        # Level 1
        self.sp_level.setValue(1)

        # Attributes
        self.on_roll_all_attributes()

        # Animal (TMNTOS)
        self.cb_animal_source.setCurrentIndex(self.cb_animal_source.findData("tmntos"))
        self.on_roll_animal_type()
        self.on_roll_animal()
        self.on_roll_name_clicked()

        # Alignment
        align_values = [
            "Principled (Good)",
            "Scrupulous (Good)",
            "Unprincipled (Selfish)",
            "Anarchist (Selfish)",
            "Miscreant (Evil)",
            "Aberrant (Evil)",
            "Diabolic (Evil)",
        ]
        chosen_align = random.choice(align_values)
        idx = self.cb_alignment.findData(chosen_align)
        self.cb_alignment.setCurrentIndex(idx if idx != -1 else 0)

        # Age/Gender (simple)
        self.ed_age.setText(str(random.randint(13, 60)))
        self.ed_gender.setText(random.choice(["Male", "Female", "Unknown"]))

        # Size
        # Do not random-roll mutant size during character generation.
        # Keep size/Bio-E based on the selected animal's baseline Bio-E data.
        self.cb_size_level.setCurrentIndex(0)
        self.cb_size_build.setCurrentIndex(1)  # Medium

        # Combat Training
        trainings = _training_names()[1:]  # exclude None
        t = random.choice(trainings) if trainings else "None"
        idx = self.cb_combat_training.findData(t)
        self.cb_combat_training.setCurrentIndex(idx if idx != -1 else 0)
        self.chk_combat_override.setChecked(False)
        self.recalc_combat_from_training()

        # 1 weapon
        if self.weapon_combos:
            weapon_names = [w["name"] for w in WEAPONS_CATALOG]
            wname = random.choice(weapon_names) if weapon_names else ""
            idx = self.weapon_combos[0].findData(wname)
            self.weapon_combos[0].setCurrentIndex(idx if idx != -1 else 0)
            for i in range(1, len(self.weapon_combos)):
                self.weapon_combos[i].setCurrentIndex(0)

        # 1 vehicle (random section)
        sections = ["landcraft", "watercraft", "aircraft"]
        chosen_section = random.choice(sections)
        if chosen_section == "landcraft":
            pool = [v["name"] for v in VEHICLES_LANDCRAFT]
        elif chosen_section == "watercraft":
            pool = [v["name"] for v in VEHICLES_WATERCRAFT]
        else:
            pool = [v["name"] for v in VEHICLES_AIRCRAFT]
        vname = random.choice(pool) if pool else ""

        for key in ("landcraft", "watercraft", "aircraft"):
            section = self.vehicle_sections.get(key, {})
            combos: list[QComboBox] = section.get("combos", [])
            for i, cb in enumerate(combos):
                if key == chosen_section and i == 0 and vname:
                    idx = cb.findData(vname)
                    cb.setCurrentIndex(idx if idx != -1 else 0)
                else:
                    cb.setCurrentIndex(0)

        self.recalc_total_wealth()
        self.recalc_weight_breakdown()
        self.statusBar().showMessage("Generated random level 1 character")

    def refresh_welcome_list(self) -> None:
        if not hasattr(self, "welcome_list"):
            return

        self.welcome_list.blockSignals(True)
        self.welcome_list.clear()

        for p in list_character_files():
            item = QListWidgetItem(p.name)
            item.setData(Qt.UserRole, p)
            self.welcome_list.addItem(item)

        self.welcome_list.blockSignals(False)


    def _enter_editor(self) -> None:
        self.stack.setCurrentWidget(self.editor_page)
        self.refresh_list()
        self.statusBar().showMessage("Editor ready")


    def go_to_start_screen(self) -> None:
        self.refresh_welcome_list()
        self.stack.setCurrentWidget(self.welcome_page)
        self.statusBar().showMessage("Start screen")


    def on_welcome_new(self) -> None:
        self._enter_editor()
        self.load_into_editor(Character(), None)


    def on_welcome_load_selected(self, _item: QListWidgetItem | None = None) -> None:
        item = self.welcome_list.currentItem()
        if item is None:
            QMessageBox.information(self, "Load", "Select a character from the list first.")
            return

        p = item.data(Qt.UserRole)
        if not isinstance(p, Path):
            p = CHARACTERS_DIR / str(item.text())

        try:
            c = load_character(p)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", f"Could not load:\n{p}\n\n{e}")
            return

        self._enter_editor()
        self.load_into_editor(c, p)
        self.refresh_list()


    def on_welcome_browse_load(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Load Character JSON",
            str(CHARACTERS_DIR),
            "JSON Files (*.json)",
        )
        if not path_str:
            return

        p = Path(path_str)
        try:
            c = load_character(p)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", f"Could not load:\n{p}\n\n{e}")
            return

        self._enter_editor()
        self.load_into_editor(c, p)
        self.refresh_list()
        self.refresh_welcome_list()

    # ---------------- Helpers ----------------
    def refresh_list(self) -> None:
        if not hasattr(self, "list_widget"):
            return
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for p in list_character_files():
            self.list_widget.addItem(p.name)
        self.list_widget.blockSignals(False)

    def confirm(self, title: str, text: str) -> bool:
        return QMessageBox.question(self, title, text) == QMessageBox.Yes
    

    def sync_defense_summary_fields(self) -> None:
        base_sdc = int(self.sp_sdc.value()) if hasattr(self, "sp_sdc") else 0
        armor_ar = int(self.sp_armor_ar.value()) if hasattr(self, "sp_armor_ar") else 0
        armor_sdc = int(self.sp_armor_sdc.value()) if hasattr(self, "sp_armor_sdc") else 0

        shield_sdc = 0
        if hasattr(self, "lbl_shield_sdc"):
            text = self.lbl_shield_sdc.text().strip()
            match = re.search(r"(\d+)", text)
            if match:
                shield_sdc = int(match.group(1))

        if hasattr(self, "ed_basic_armor_ar"):
            self.ed_basic_armor_ar.setText(str(armor_ar))

        if hasattr(self, "ed_basic_armor_sdc"):
            self.ed_basic_armor_sdc.setText(str(armor_sdc))

        if hasattr(self, "ed_basic_shield_sdc"):
            self.ed_basic_shield_sdc.setText(str(shield_sdc))

        if hasattr(self, "ed_basic_total_sdc"):
            self.ed_basic_total_sdc.setText(str(base_sdc + armor_sdc + shield_sdc))


    
    # ---------------- Actions ----------------
    def on_new(self) -> None:
        if self.confirm("New Character", "Discard current edits and start a new character?"):
            if hasattr(self, "skill_effect_rolls"):
                self.skill_effect_rolls.clear()
            self.load_into_editor(Character(), None)

    def on_select_character(self) -> None:
        items = self.list_widget.selectedItems()
        if not items:
            return

        filename = items[0].text()
        path = CHARACTERS_DIR / filename
        try:
            c = load_character(path)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", f"Could not load {filename}\n\n{e}")
            return

        self.load_into_editor(c, path)

    def on_load_dialog(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Load Character JSON",
            str(CHARACTERS_DIR),
            "JSON Files (*.json)",
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            c = load_character(path)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", f"Could not load:\n{path}\n\n{e}")
            return

        if hasattr(self, "skill_effect_rolls"):
            self.skill_effect_rolls.clear()

        self.load_into_editor(c, path)
        self.refresh_list()
        self.refresh_welcome_list()

    def on_save(self) -> None:
        c = self.editor_to_character()

        if self.current_path is None:
            filename = c.default_filename()
            path = CHARACTERS_DIR / filename
        else:
            path = self.current_path

        if not c.name.strip():
            if not self.confirm("No Name", "Character has no name. Save anyway?"):
                return

        try:
            save_character(c, path)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Could not save:\n{path}\n\n{e}")
            return

        self.load_into_editor(c, path)
        self.refresh_list()
        self.refresh_welcome_list()

    def on_save_as(self) -> None:
        c = self.editor_to_character()

        suggested = str(CHARACTERS_DIR / c.default_filename())
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save Character As",
            suggested,
            "JSON Files (*.json)",
        )
        if not path_str:
            return

        path = Path(path_str)
        if path.suffix.lower() != ".json":
            path = path.with_suffix(".json")

        try:
            save_character(c, path)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", f"Could not save:\n{path}\n\n{e}")
            return

        self.load_into_editor(c, path)
        self.refresh_list()
        self.refresh_welcome_list()

    def on_delete(self) -> None:
        if self.current_path is None:
            QMessageBox.information(self, "Delete", "This character isn’t saved yet.")
            return

        if not self.confirm("Delete Character", f"Delete file?\n\n{self.current_path.name}"):
            return

        try:
            delete_character_file(self.current_path)
        except Exception as e:
            QMessageBox.critical(self, "Delete failed", f"Could not delete:\n{self.current_path}\n\n{e}")
            return

        if hasattr(self, "skill_effect_rolls"):
            self.skill_effect_rolls.clear()

        self.load_into_editor(Character(), None)
        self.refresh_list()
        self.refresh_welcome_list()

    def on_load_character_art(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Character Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not path:
            return

        pix = QPixmap(path)
        if pix.isNull():
            return

        scaled = pix.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl_character_art.setPixmap(scaled)
        self.current_character.image_path = path

    def on_clear_character_art(self) -> None:
        self.lbl_character_art.clear()
        self.lbl_character_art.setText("Character Art\n240x240")
        self.current_character.image_path = None


    def _all_selected_skill_names(self) -> list[str]:
        names: list[str] = []

        for cb in getattr(self, "pro_skill_boxes", []):
            name = self._selected_skill_name(cb)
            if name:
                names.append(name)

        for cb in getattr(self, "amateur_skill_boxes", []):
            name = self._selected_skill_name(cb)
            if name:
                names.append(name)

        return names


    def _roll_skill_effect_expr(self, expr: str) -> int:
        total, detail = self.eval_dice_expression(expr)
        self.log_roll(f"[Skill Bonus] {expr} -> {detail} Total = {total}")
        return total


    def _ensure_skill_effect_rolls(self) -> None:
        if not hasattr(self, "skill_effect_rolls"):
            self.skill_effect_rolls: dict[str, dict[str, int]] = {}


    def _refresh_skill_effect_roll_cache(self) -> None:
        self._ensure_skill_effect_rolls()

        selected = set(self._all_selected_skill_names())
        effects = globals().get("PHYSICAL_SKILL_EFFECTS", {})

        for skill_name in list(self.skill_effect_rolls.keys()):
            if skill_name not in selected:
                del self.skill_effect_rolls[skill_name]

        for skill_name in selected:
            effect = effects.get(skill_name)
            if not effect:
                continue

            if skill_name not in self.skill_effect_rolls:
                self.skill_effect_rolls[skill_name] = {}

            cache = self.skill_effect_rolls[skill_name]

            for key, expr_key in (
                ("sdc_roll", "sdc_roll"),
                ("speed_roll", "speed_roll"),
                ("swim_speed_roll", "swim_speed_roll"),
            ):
                expr = effect.get(expr_key)
                if isinstance(expr, str) and key not in cache:
                    cache[key] = self._roll_skill_effect_expr(expr)

            attr_rolls = effect.get("attribute_rolls", {})
            if isinstance(attr_rolls, dict):
                for attr_name, expr in attr_rolls.items():
                    cache_key = f"attr_{attr_name}"
                    if isinstance(expr, str) and cache_key not in cache:
                        cache[cache_key] = self._roll_skill_effect_expr(expr)


    def _get_physical_skill_totals(self) -> dict[str, Any]:
        self._refresh_skill_effect_roll_cache()
        effects = globals().get("PHYSICAL_SKILL_EFFECTS", {})

        totals: dict[str, Any] = {
            "attributes": {"IQ": 0, "ME": 0, "MA": 0, "PS": 0, "PP": 0, "PE": 0, "PB": 0, "Speed": 0},
            "combat": {
                "strike": 0,
                "parry": 0,
                "dodge": 0,
                "initiative": 0,
                "actions_per_round": 0,
                "roll_with_impact": 0,
                "pull_punch": 0,
                "strike_swords": 0,
                "parry_swords": 0,
                "damage_swords": 0,
            },
            "sdc_bonus": 0,
            "speed_bonus": 0,
            "swim_speed_bonus": 0,
            "skill_pct_bonus": {},
            "extra_attacks": [],
            "notes": [],
        }

        for skill_name in self._all_selected_skill_names():
            effect = effects.get(skill_name)
            if not effect:
                continue

            for attr_name, amount in effect.get("attribute_bonus", {}).items():
                key = "Speed" if attr_name == "Spd" else attr_name
                if key in totals["attributes"] and isinstance(amount, int):
                    totals["attributes"][key] += amount

            for attr_name in effect.get("attribute_rolls", {}):
                cache_key = f"attr_{attr_name}"
                rolled = self.skill_effect_rolls.get(skill_name, {}).get(cache_key, 0)
                key = "Speed" if attr_name == "Spd" else attr_name
                if key in totals["attributes"]:
                    totals["attributes"][key] += int(rolled)

            for combat_key, amount in effect.get("combat_bonus", {}).items():
                if combat_key in totals["combat"] and isinstance(amount, int):
                    totals["combat"][combat_key] += amount

            totals["sdc_bonus"] += int(effect.get("sdc_flat", 0) or 0)
            totals["sdc_bonus"] += int(self.skill_effect_rolls.get(skill_name, {}).get("sdc_roll", 0) or 0)
            totals["speed_bonus"] += int(self.skill_effect_rolls.get(skill_name, {}).get("speed_roll", 0) or 0)
            totals["swim_speed_bonus"] += int(self.skill_effect_rolls.get(skill_name, {}).get("swim_speed_roll", 0) or 0)

            for skill_key, pct_bonus in effect.get("skill_bonus_pct", {}).items():
                totals["skill_pct_bonus"][skill_key] = totals["skill_pct_bonus"].get(skill_key, 0) + int(pct_bonus)

            for attack_name in effect.get("extra_attacks", []):
                if attack_name not in totals["extra_attacks"]:
                    totals["extra_attacks"].append(attack_name)

            for note in effect.get("notes", []):
                if note not in totals["notes"]:
                    totals["notes"].append(f"{skill_name}: {note}")

        return totals


    def get_effective_attribute(self, attr_name: str) -> int:
        base = 0
        if attr_name in self.attribute_fields:
            base = int(self.attribute_fields[attr_name].value())

        totals = self._get_physical_skill_totals()
        bonus = int(totals["attributes"].get(attr_name, 0))
        return base + bonus
    
    def _normalize_animal_for_names(self, animal_label: str) -> str:
        s = (animal_label or "").strip().upper()

        direct = {
            "POND TURTLE": "POND TURTLE",
            "TURTLE": "POND TURTLE",
            "SNAPPING TURTLE": "SNAPPING TURTLE",
            "RAT": "RAT",
            "RABBIT": "RABBIT",
            "RACCOON": "RACCOON",
            "FOX": "FOX",
            "WOLF": "WOLF",
            "DOG": "DOG",
            "CAT": "CAT",
            "ALLIGATOR": "ALLIGATOR",
            "CROCODILE": "CROCODILE",
            "BAT": "BAT",
            "BLACK BEAR": "BEAR",
            "GRIZZLY BEAR": "BEAR",
            "BROWN BEAR": "BEAR",
            "POLAR BEAR": "BEAR",
            "BEAR": "BEAR",
            "SKUNK": "SKUNK",
            "OTTER": "OTTER",
            "AARDVARK": "AARDVARK",
            "FROG": "FROG",
            "TOAD": "TOAD",
            "SALAMANDER": "SALAMANDER",
            "NEWT": "NEWT",
            "AXOLOTL": "AXOLOTL",
            "CHIMPANZEE": "CHIMPANZEE",
            "GORILLA": "GORILLA",
            "ORANGUTAN": "ORANGUTAN",
            "ARMADILLO": "ARMADILLO",
            "BADGER": "BADGER",
            "BEAVER": "BEAVER",
            "BUFFALO": "BUFFALO",
            "BISON": "BISON",
            "CAMEL": "CAMEL",
            "ELEPHANT": "ELEPHANT",
            "BOBCAT": "BOBCAT",
            "LYNX": "LYNX",
            "CHEETAH": "CHEETAH",
            "COUGAR": "COUGAR",
            "JAGUAR": "JAGUAR",
            "LEOPARD": "LEOPARD",
            "LION": "LION",
            "TIGER": "TIGER",
            "GOAT": "GOAT",
            "HIPPOPOTAMUS": "HIPPOPOTAMUS",
            "HORSE": "HORSE",
            "LEMUR": "LEMUR",
            "GECKO": "GECKO",
            "SKINK": "SKINK",
            "CHAMELEON": "CHAMELEON",
            "GILA MONSTER": "GILA MONSTER",
            "IGUANA": "IGUANA",
            "KOMODO DRAGON": "KOMODO DRAGON",
            "MARTEN": "MARTEN",
            "MINK": "MINK",
            "MOLE": "MOLE",
            "MONKEY": "MONKEY",
            "BABOON": "BABOON",
            "MUSKRAT": "MUSKRAT",
            "PIG": "PIG",
            "BOAR": "BOAR",
            "PORCUPINE": "PORCUPINE",
            "OPOSSUM": "OPOSSUM",
            "SHARK": "SHARK",
            "SHEEP": "SHEEP",
            "SQUIRREL": "SQUIRREL",
            "WEASEL": "WEASEL",
            "FERRET": "FERRET",
            "WOLVERINE": "WOLVERINE",
            "MOUSE": "MOUSE",
            "GERBIL": "GERBIL",
            "HAMSTER": "HAMSTER",
            "GUINEA PIG": "GUINEA PIG",
            "PIKA": "PIKA",
        }

        if s in direct:
            return direct[s]

        for k in direct:
            if k in s:
                return direct[k]

        return ""

    def on_roll_name_clicked(self) -> None:
        animal_label = ""
        if hasattr(self, "cb_animal") and self.cb_animal is not None:
            animal_label = self.cb_animal.currentText()

        key = self._normalize_animal_for_names(animal_label)
        pool = ANIMAL_NAME_POOLS.get(key, [])

        if not pool:
            if not self.ed_name.text().strip():
                self.ed_name.setText("—")
            return

        self.ed_name.setText(random.choice(pool))   

    def on_bioe_animal_selected(self) -> None:
        """
        Called when the selected animal changes.
        Updates the Bio-E tab data for the new animal.
        """

        animal = self.cb_animal.currentData()
        if not animal:
            return

        try:
            self.load_bioe_animal_data(animal)
        except Exception:
            pass

        if hasattr(self, "recalc_bioe_spent"):
            self.recalc_bioe_spent()


    def on_roll_size_clicked(self) -> None:
        """
        Roll a random size level/build for manual use from the Basics tab.
        This does not affect Bio-E random generation unless the user clicks it.
        """
        size_level = random.randint(1, 20)
        size_build = random.choice(["short", "medium", "long"])

        idx = self.cb_size_level.findData(size_level)
        if idx != -1:
            self.cb_size_level.setCurrentIndex(idx)

        idx = self.cb_size_build.findData(size_build)
        if idx != -1:
            self.cb_size_build.setCurrentIndex(idx)

        self.statusBar().showMessage(
            f"Rolled size: Level {size_level}, {size_build.title()}",
            3000,
        )


        

    # ---------------- Editor page ----------------
    def _build_editor_page(self) -> None:
        layout = QHBoxLayout(self.editor_page)

        # ---------------- Left: dice tools + notes ----------------
        left = QVBoxLayout()
        layout.addLayout(left, 1)

        dice_box = QGroupBox("Dice Tools")
        dice_layout = QVBoxLayout(dice_box)

        self.roll_log = QTextEdit()
        self.roll_log.setReadOnly(True)
        self.roll_log.setPlaceholderText("Roll log…")
        self.roll_log.setMinimumHeight(140)
        dice_layout.addWidget(self.roll_log)

        grid = QGridLayout()
        dice_layout.addLayout(grid)

        self.dice_counts: dict[int, QSpinBox] = {}
        die_faces = [2, 4, 6, 8, 10, 12, 20, 100]

        for idx, faces in enumerate(die_faces):
            r = idx // 4
            c = (idx % 4) * 2

            sp = QSpinBox()
            sp.setRange(0, 200)
            sp.setValue(0)
            sp.setToolTip(f"How many d{faces} to roll")
            self.dice_counts[faces] = sp

            btn = QPushButton(f"Roll d{faces}")
            btn.clicked.connect(lambda _=False, f=faces: self.on_roll_generic_die(f))

            grid.addWidget(sp, r, c)
            grid.addWidget(btn, r, c + 1)

        btn_row = QHBoxLayout()
        self.btn_clear_log = QPushButton("Clear Log")
        self.btn_clear_log.clicked.connect(self.roll_log.clear)
        btn_row.addWidget(self.btn_clear_log)
        dice_layout.addLayout(btn_row)
        left.addWidget(dice_box)

        # ---------------- Left bottom: Notes ----------------
        notes_box = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_box)

        self.ed_notes = QTextEdit()
        self.ed_notes.setPlaceholderText("Notes…")
        notes_layout.addWidget(self.ed_notes, 1)

        left.addWidget(notes_box, 1)

        # ---------------- Right: tabbed editor ----------------
        right = QVBoxLayout()
        layout.addLayout(right, 2)

        self.tabs = QTabWidget()
        right.addWidget(self.tabs, 1)

        self.tab_basics = QWidget()
        self.tab_attributes = QWidget()
        self.tab_skills = QWidget()
        self.tab_combat = QWidget()
        self.tab_bioe = QWidget()
        self.tab_equipment = QWidget()
        self.tab_vehicles = QWidget()

        self.tabs.addTab(self.tab_basics, "Basics")
        self.tabs.addTab(self.tab_attributes, "Attributes")
        self.tabs.addTab(self.tab_skills, "Skills")
        self.tabs.addTab(self.tab_combat, "Combat")
        self.tabs.addTab(self.tab_bioe, "Bio-E / Mutant")
        self.tabs.addTab(self.tab_equipment, "Equipment")
        self.tabs.addTab(self.tab_vehicles, "Vehicles")

        # ===================== Basics tab =====================
        self.basics_layout = self.make_scrollable_tab(self.tab_basics)
        basics_form = QFormLayout()
        self.basics_layout.addLayout(basics_form)

        # ---- Character Art ----
        art_row = QWidget()
        art_layout = QVBoxLayout()
        art_layout.setContentsMargins(0, 0, 0, 0)
        art_row.setLayout(art_layout)

        self.lbl_character_art = QLabel()
        self.lbl_character_art.setFixedSize(240, 240)
        self.lbl_character_art.setAlignment(Qt.AlignCenter)
        self.lbl_character_art.setStyleSheet(
            "border: 1px solid #444; background-color: #222;"
        )
        self.lbl_character_art.setText("Character Art\n240x240")

        btn_row = QWidget()
        btn_row_l = QHBoxLayout()
        btn_row_l.setContentsMargins(0, 0, 0, 0)
        btn_row.setLayout(btn_row_l)

        self.btn_load_art = QPushButton("Load Image")
        self.btn_clear_art = QPushButton("Clear")

        self.btn_load_art.clicked.connect(self.on_load_character_art)
        self.btn_clear_art.clicked.connect(self.on_clear_character_art)

        btn_row_l.addWidget(self.btn_load_art)
        btn_row_l.addWidget(self.btn_clear_art)

        art_layout.addWidget(self.lbl_character_art, 0, Qt.AlignCenter)
        art_layout.addWidget(btn_row)

        basics_form.addRow("Character Art", art_row)

        name_row = QWidget()
        name_l = QHBoxLayout()
        name_l.setContentsMargins(0, 0, 0, 0)
        name_row.setLayout(name_l)

        self.ed_name = QLineEdit()
        self.btn_roll_name = QPushButton("Roll")
        self.btn_roll_name.clicked.connect(self.on_roll_name_clicked)

        name_l.addWidget(self.ed_name, 1)
        name_l.addWidget(self.btn_roll_name, 0)

        basics_form.addRow("Name", name_row)

        self.cb_animal_source = QComboBox()
        self.cb_animal_source.addItem("Select your source", "")
        self.cb_animal_source.addItem("Teenage Mutant Ninja Turtles & Other Strangeness", "tmntos")
        self.cb_animal_source.addItem("Teenage Mutant Ninja Turtles Transdimensional Adventures", "tmnttda")
        self.cb_animal_source.currentIndexChanged.connect(self.on_animal_source_changed)
        basics_form.addRow("Animal Source", self.cb_animal_source)

        animal_type_row = QWidget()
        animal_type_l = QHBoxLayout()
        animal_type_l.setContentsMargins(0, 0, 0, 0)
        animal_type_row.setLayout(animal_type_l)

        self.cb_animal_type = QComboBox()
        self.cb_animal_type.addItem("Roll or select your animal type", "")
        self.cb_animal_type.currentIndexChanged.connect(self.on_animal_type_changed)

        self.btn_roll_animal_type = QPushButton("Roll")
        self.btn_roll_animal_type.clicked.connect(self.on_roll_animal_type)

        animal_type_l.addWidget(self.cb_animal_type, 1)
        animal_type_l.addWidget(self.btn_roll_animal_type, 0)
        basics_form.addRow("Animal Type", animal_type_row)

        animal_row = QWidget()
        animal_l = QHBoxLayout()
        animal_l.setContentsMargins(0, 0, 0, 0)
        animal_row.setLayout(animal_l)

        self.cb_animal = QComboBox()
        self.cb_animal.addItem("Roll or select your animal", "")
        self.cb_animal.currentIndexChanged.connect(self.on_bioe_animal_selected)

        self.btn_roll_animal = QPushButton("Roll")
        self.btn_roll_animal.clicked.connect(self.on_roll_animal)

        animal_l.addWidget(self.cb_animal, 1)
        animal_l.addWidget(self.btn_roll_animal, 0)
        basics_form.addRow("Animal", animal_row)

        self.cb_alignment = QComboBox()
        self.cb_alignment.addItem("Select alignment", "")
        self.cb_alignment.addItem("Principled (Good)", "Principled (Good)")
        self.cb_alignment.addItem("Scrupulous (Good)", "Scrupulous (Good)")
        self.cb_alignment.addItem("Unprincipled (Selfish)", "Unprincipled (Selfish)")
        self.cb_alignment.addItem("Anarchist (Selfish)", "Anarchist (Selfish)")
        self.cb_alignment.addItem("Miscreant (Evil)", "Miscreant (Evil)")
        self.cb_alignment.addItem("Aberrant (Evil)", "Aberrant (Evil)")
        self.cb_alignment.addItem("Diabolic (Evil)", "Diabolic (Evil)")
        basics_form.addRow("Alignment", self.cb_alignment)

        self.ed_age = QLineEdit()
        basics_form.addRow("Age", self.ed_age)

        self.ed_gender = QLineEdit()
        basics_form.addRow("Gender", self.ed_gender)

        size_row = QWidget()
        size_row_layout = QHBoxLayout()
        size_row_layout.setContentsMargins(0, 0, 0, 0)
        size_row.setLayout(size_row_layout)

        self.cb_size_level = QComboBox()
        for lvl in range(1, 21):
            self.cb_size_level.addItem(str(lvl), lvl)

        self.cb_size_build = QComboBox()
        self.cb_size_build.addItem("Short", "short")
        self.cb_size_build.addItem("Medium", "medium")
        self.cb_size_build.addItem("Long", "long")

        self.btn_roll_size = QPushButton("Roll")
        self.btn_roll_size.clicked.connect(self.on_roll_size_clicked)

        size_row_layout.addWidget(QLabel("Level"))
        size_row_layout.addWidget(self.cb_size_level)
        size_row_layout.addSpacing(8)
        size_row_layout.addWidget(QLabel("Build"))
        size_row_layout.addWidget(self.cb_size_build)
        size_row_layout.addStretch(1)
        size_row_layout.addWidget(self.btn_roll_size)

        basics_form.addRow("Size", size_row)

        self.ed_weight = QLineEdit()
        basics_form.addRow("Weight", self.ed_weight)

        self.ed_height = QLineEdit()
        basics_form.addRow("Height", self.ed_height)

        self.sp_total_credits = QSpinBox()
        self.sp_total_credits.setRange(0, 2_000_000_000)
        self.sp_total_credits.valueChanged.connect(self.recalc_total_wealth)
        basics_form.addRow("Total Credits", self.sp_total_credits)

        self.ed_total_wealth = QLineEdit()
        self.ed_total_wealth.setReadOnly(True)
        basics_form.addRow("Total Wealth", self.ed_total_wealth)

        self.sp_xp = QSpinBox()
        self.sp_xp.setRange(0, 10_000_000)
        basics_form.addRow("XP", self.sp_xp)

        self.sp_level = QSpinBox()
        self.sp_level.setRange(1, 99)
        self.sp_level.valueChanged.connect(self.recalc_skill_displays)
        self.sp_level.valueChanged.connect(self.recalc_combat_from_training)
        basics_form.addRow("Level", self.sp_level)

        hp_row = QWidget()
        hp_row_l = QHBoxLayout()
        hp_row_l.setContentsMargins(0, 0, 0, 0)
        hp_row.setLayout(hp_row_l)

        self.sp_hp = QSpinBox()
        self.sp_hp.setRange(0, 100_000)

        self.btn_roll_hp = QPushButton("Roll")
        self.btn_roll_hp.setToolTip("Roll 1d6 and add to PE to determine HP")
        self.btn_roll_hp.clicked.connect(self.on_roll_hp_clicked)

        hp_row_l.addWidget(self.sp_hp, 1)
        hp_row_l.addWidget(self.btn_roll_hp, 0)

        basics_form.addRow("Hit Points", hp_row)

        self.sp_sdc = QSpinBox()
        self.sp_sdc.setRange(0, 100_000)
        self.sp_sdc.valueChanged.connect(self.sync_defense_summary_fields)
        basics_form.addRow("Base SDC", self.sp_sdc)

        self.ed_basic_armor_ar = QLineEdit()
        self.ed_basic_armor_ar.setReadOnly(True)
        basics_form.addRow("Armor AR", self.ed_basic_armor_ar)

        self.ed_basic_armor_sdc = QLineEdit()
        self.ed_basic_armor_sdc.setReadOnly(True)
        basics_form.addRow("Armor SDC", self.ed_basic_armor_sdc)

        self.ed_basic_shield_sdc = QLineEdit()
        self.ed_basic_shield_sdc.setReadOnly(True)
        basics_form.addRow("Shield SDC", self.ed_basic_shield_sdc)

        self.ed_basic_total_sdc = QLineEdit()
        self.ed_basic_total_sdc.setReadOnly(True)
        basics_form.addRow("Total SDC", self.ed_basic_total_sdc)

        self.basics_layout.addStretch(1)

        # ===================== Attributes tab =====================
        self.attributes_layout = self.make_scrollable_tab(self.tab_attributes)
        attr_form = QFormLayout()
        self.attributes_layout.addLayout(attr_form)
        self.attribute_fields: dict[str, QSpinBox] = {}

        for attr in ["IQ", "ME", "MA", "PS", "PP", "PE", "PB", "Speed"]:
            sp = QSpinBox()
            sp.setRange(0, 100)
            sp.valueChanged.connect(self.recalc_skill_displays)

            row = QWidget()
            row_l = QHBoxLayout()
            row_l.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_l)

            btn = QPushButton("Roll")
            btn.setToolTip("Roll attribute (3d6; if 16–18 add +1d6)")
            btn.clicked.connect(lambda _=False, a=attr: self.on_roll_single_attribute(a))

            row_l.addWidget(sp, 1)
            row_l.addWidget(btn, 0)

            attr_form.addRow(attr, row)
            self.attribute_fields[attr] = sp

        self.btn_roll_all_attributes = QPushButton("Roll All")
        self.btn_roll_all_attributes.setToolTip("Roll all attributes (3d6; if 16–18 add +1d6).")
        self.btn_roll_all_attributes.clicked.connect(self.on_roll_all_attributes)
        attr_form.addRow("", self.btn_roll_all_attributes)
        self.attributes_layout.addStretch(1)

        # ===================== Skills tab =====================
        self.skills_layout = self.make_scrollable_tab(self.tab_skills)
        skills_layout = self.skills_layout

        self._load_skill_rules()
        self._build_skill_models()

        skills_layout.addWidget(QLabel("Professional Skills (10)"))
        pro_form = QFormLayout()
        self.pro_skill_boxes = []
        self.pro_skill_pct_labels = []

        for i in range(10):
            cb = QComboBox()
            cb.setModel(self.pro_model)
            cb.currentIndexChanged.connect(self.on_skills_changed)

            pct = QLabel("—")
            pct.setMinimumWidth(70)

            btn_roll = QPushButton("Roll")
            btn_roll.setMaximumWidth(70)
            btn_roll.clicked.connect(
                lambda _=False, c=cb: self.on_roll_skill_check(c, self.pro_skill_lookup)
            )

            row = QWidget()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.addWidget(cb, 1)
            row_l.addWidget(pct, 0)
            row_l.addWidget(btn_roll, 0)

            self.pro_skill_boxes.append(cb)
            self.pro_skill_pct_labels.append(pct)
            pro_form.addRow(f"Pro {i+1}", row)

        skills_layout.addLayout(pro_form)
        skills_layout.addWidget(QLabel(""))

        skills_layout.addWidget(QLabel("Amateur Skills (15)"))
        ama_form = QFormLayout()
        self.amateur_skill_boxes = []
        self.amateur_skill_pct_labels = []

        for i in range(15):
            cb = QComboBox()
            cb.setModel(self.amateur_model)
            cb.currentIndexChanged.connect(self.on_skills_changed)

            pct = QLabel("—")
            pct.setMinimumWidth(70)

            btn_roll = QPushButton("Roll")
            btn_roll.setMaximumWidth(70)
            btn_roll.clicked.connect(
                lambda _=False, c=cb: self.on_roll_skill_check(c, self.amateur_skill_lookup)
            )

            row = QWidget()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 0, 0, 0)
            row_l.addWidget(cb, 1)
            row_l.addWidget(pct, 0)
            row_l.addWidget(btn_roll, 0)

            self.amateur_skill_boxes.append(cb)
            self.amateur_skill_pct_labels.append(pct)
            ama_form.addRow(f"Amateur {i+1}", row)

        skills_layout.addLayout(ama_form)
        skills_layout.addStretch(1)

        # ===================== Combat tab =====================
        self.combat_layout = self.make_scrollable_tab(self.tab_combat)
        combat_form = QFormLayout()
        self.combat_layout.addLayout(combat_form)

        self.cb_combat_training = QComboBox()
        for name in _training_names():
            self.cb_combat_training.addItem(name, name)

        self.ed_combat_training_details = QTextEdit()
        self.ed_combat_training_details.setReadOnly(False)
        self.ed_combat_training_details.setMinimumHeight(180)

        combat_form.addRow("Combat Training", self.cb_combat_training)
        combat_form.addRow("Training Details", self.ed_combat_training_details)

        self.chk_combat_auto_details = QCheckBox("Auto-generate Training Details")
        self.chk_combat_auto_details.setChecked(True)
        self.chk_combat_auto_details.toggled.connect(lambda _=False: self.recalc_combat_from_training())
        combat_form.addRow("", self.chk_combat_auto_details)

        self.chk_combat_override = QCheckBox("Override derived combat values (manual edit)")
        self.chk_combat_override.setChecked(False)
        self.chk_combat_override.toggled.connect(self.on_toggle_combat_override)
        combat_form.addRow("", self.chk_combat_override)

        self.cb_combat_training.currentIndexChanged.connect(self.recalc_combat_from_training)

        self.sp_strike = QSpinBox()
        self.sp_parry = QSpinBox()
        self.sp_dodge = QSpinBox()
        self.sp_initiative = QSpinBox()
        self.sp_actions = QSpinBox()

        for sp in [self.sp_strike, self.sp_parry, self.sp_dodge, self.sp_initiative, self.sp_actions]:
            sp.setRange(-50, 50)

        combat_form.addRow("Strike", self.sp_strike)
        combat_form.addRow("Parry", self.sp_parry)
        combat_form.addRow("Dodge", self.sp_dodge)
        combat_form.addRow("Initiative", self.sp_initiative)
        combat_form.addRow("Actions per Round", self.sp_actions)
        techniques_box = QGroupBox("Combat Techniques / Special Attacks")
        techniques_layout = QVBoxLayout(techniques_box)

        self.lw_combat_techniques = QListWidget()
        techniques_layout.addWidget(self.lw_combat_techniques)

        combat_form.addRow("", techniques_box)
        self._set_combat_spinboxes_editable(False)
        self.combat_layout.addStretch(1)

        # ===================== Bio-E tab =====================
        self.bioe_layout = self.make_scrollable_tab(self.tab_bioe)
        bio_outer = self.bioe_layout

        totals_box = QGroupBox("Bio-E Totals")
        totals_form = QFormLayout(totals_box)

        self.sp_bio_total = QSpinBox()
        self.sp_bio_spent = QSpinBox()
        self.sp_bio_total.setRange(0, 100000)
        self.sp_bio_spent.setRange(0, 100000)
        self.sp_bio_total.valueChanged.connect(self.recalc_bioe_spent)

        self.lbl_bio_remaining = QLabel("Remaining: 0")
        self.lbl_bio_remaining.setMinimumWidth(180)

        totals_row = QWidget()
        totals_row_l = QHBoxLayout()
        totals_row_l.setContentsMargins(0, 0, 0, 0)
        totals_row.setLayout(totals_row_l)
        totals_row_l.addWidget(self.sp_bio_total, 0)
        totals_row_l.addSpacing(12)
        totals_row_l.addWidget(self.lbl_bio_remaining, 1)

        totals_form.addRow("Total Bio-E", totals_row)
        totals_form.addRow("Spent Bio-E", self.sp_bio_spent)

        bio_outer.addWidget(totals_box)

        original_box = QGroupBox("Original Animal Characteristics")
        original_form = QFormLayout(original_box)

        self.ed_bio_orig_size_level = QLineEdit()
        self.ed_bio_orig_size_level.setReadOnly(True)

        self.ed_bio_orig_length = QLineEdit()
        self.ed_bio_orig_length.setReadOnly(True)

        self.ed_bio_orig_weight = QLineEdit()
        self.ed_bio_orig_weight.setReadOnly(True)

        self.ed_bio_orig_build = QLineEdit()
        self.ed_bio_orig_build.setReadOnly(True)

        original_form.addRow("Size Level", self.ed_bio_orig_size_level)
        original_form.addRow("Length", self.ed_bio_orig_length)
        original_form.addRow("Weight", self.ed_bio_orig_weight)
        original_form.addRow("Build", self.ed_bio_orig_build)

        bio_outer.addWidget(original_box)

        size_box = QGroupBox("Size Levels (Bio-E Spend)")
        size_form = QFormLayout(size_box)

        self.cb_bio_mutant_size_level = QComboBox()
        for lvl in range(1, 21):
            self.cb_bio_mutant_size_level.addItem(str(lvl), lvl)
        self.lbl_bio_size_cost = QLabel("Cost: 0")
        self.lbl_bio_size_cost.setMinimumWidth(120)

        size_row = QWidget()
        size_row_l = QHBoxLayout()
        size_row_l.setContentsMargins(0, 0, 0, 0)
        size_row.setLayout(size_row_l)
        size_row_l.addWidget(self.cb_bio_mutant_size_level, 1)
        size_row_l.addWidget(self.lbl_bio_size_cost, 0)

        self.cb_bio_mutant_size_level.currentIndexChanged.connect(self.recalc_bioe_spent)
        size_form.addRow("Mutant Size Level", size_row)

        bio_outer.addWidget(size_box)

        mutant_box = QGroupBox("Mutant Changes & Costs")
        mutant_l = QVBoxLayout(mutant_box)
        self.ed_bio_mutant_changes = QTextEdit()
        self.ed_bio_mutant_changes.setReadOnly(True)
        self.ed_bio_mutant_changes.setMinimumHeight(110)
        mutant_l.addWidget(self.ed_bio_mutant_changes)

        bio_outer.addWidget(mutant_box)

        bonus_box = QGroupBox("Attribute Bonuses")
        bonus_form = QFormLayout(bonus_box)
        self.ed_bio_attr_bonus = QTextEdit()
        self.ed_bio_attr_bonus.setReadOnly(True)
        self.ed_bio_attr_bonus.setMinimumHeight(70)
        bonus_form.addRow("", self.ed_bio_attr_bonus)
        bio_outer.addWidget(bonus_box)

        human_box = QGroupBox("Human Features")
        human_form = QFormLayout(human_box)

        self.cb_human_hands = QComboBox()
        self.cb_human_biped = QComboBox()
        self.cb_human_speech = QComboBox()
        self.cb_human_looks = QComboBox()

        for cb in (self.cb_human_hands, self.cb_human_biped, self.cb_human_speech, self.cb_human_looks):
            for label, cost in HUMAN_FEATURE_OPTIONS:
                cb.addItem(label, cost)
            cb.currentIndexChanged.connect(self.recalc_bioe_spent)

        human_form.addRow("Hands", self.cb_human_hands)
        human_form.addRow("Biped", self.cb_human_biped)
        human_form.addRow("Speech", self.cb_human_speech)
        human_form.addRow("Looks", self.cb_human_looks)

        bio_outer.addWidget(human_box)

        weapons_box = QGroupBox("Natural Weapons")
        weapons_form = QFormLayout(weapons_box)

        self.bio_weapon_combos = []
        self.bio_weapon_cost_labels = []
        self.bio_weapon_detail_boxes = []

        for i in range(5):
            row = QWidget()
            row_l = QVBoxLayout()
            row_l.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_l)

            top = QWidget()
            top_l = QHBoxLayout()
            top_l.setContentsMargins(0, 0, 0, 0)
            top.setLayout(top_l)

            cb = QComboBox()
            cb.addItem("None", None)
            cb.currentIndexChanged.connect(self.recalc_bioe_spent)

            cost_lbl = QLabel("0")
            cost_lbl.setMinimumWidth(80)

            top_l.addWidget(cb, 1)
            top_l.addWidget(QLabel("Cost:"), 0)
            top_l.addWidget(cost_lbl, 0)

            details = QTextEdit()
            details.setReadOnly(True)
            details.setMinimumHeight(45)

            row_l.addWidget(top)
            row_l.addWidget(details)

            self.bio_weapon_combos.append(cb)
            self.bio_weapon_cost_labels.append(cost_lbl)
            self.bio_weapon_detail_boxes.append(details)

            weapons_form.addRow(f"Natural Weapon {i+1}", row)

        bio_outer.addWidget(weapons_box)

        abilities_box = QGroupBox("Animal Abilities")
        abilities_form = QFormLayout(abilities_box)

        self.bio_ability_combos = []
        self.bio_ability_cost_labels = []
        self.bio_ability_detail_boxes = []

        for i in range(10):
            row = QWidget()
            row_l = QVBoxLayout()
            row_l.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_l)

            top = QWidget()
            top_l = QHBoxLayout()
            top_l.setContentsMargins(0, 0, 0, 0)
            top.setLayout(top_l)

            cb = QComboBox()
            cb.addItem("None", None)
            cb.currentIndexChanged.connect(self.recalc_bioe_spent)

            cost_lbl = QLabel("0")
            cost_lbl.setMinimumWidth(80)

            top_l.addWidget(cb, 1)
            top_l.addWidget(QLabel("Cost:"), 0)
            top_l.addWidget(cost_lbl, 0)

            details = QTextEdit()
            details.setReadOnly(True)
            details.setMinimumHeight(45)

            row_l.addWidget(top)
            row_l.addWidget(details)

            self.bio_ability_combos.append(cb)
            self.bio_ability_cost_labels.append(cost_lbl)
            self.bio_ability_detail_boxes.append(details)

            abilities_form.addRow(f"Ability {i+1}", row)

        bio_outer.addWidget(abilities_box)

        psionics_box = QGroupBox("Psionic Powers (ME 12+ required)")
        psionics_form = QFormLayout(psionics_box)

        self.bio_psionic_combos = []
        self.bio_psionic_cost_labels = []

        for i in range(5):
            row = QWidget()
            row_l = QHBoxLayout()
            row_l.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_l)

            cb = QComboBox()
            for label, cost in PSIONIC_POWER_OPTIONS:
                cb.addItem(label, cost)
            cb.currentIndexChanged.connect(self.recalc_bioe_spent)

            cost_lbl = QLabel("0")
            cost_lbl.setMinimumWidth(80)

            row_l.addWidget(cb, 1)
            row_l.addWidget(QLabel("Cost:"), 0)
            row_l.addWidget(cost_lbl, 0)

            self.bio_psionic_combos.append(cb)
            self.bio_psionic_cost_labels.append(cost_lbl)

            psionics_form.addRow(f"Psionic {i+1}", row)

        bio_outer.addWidget(psionics_box)

        traits_box = QGroupBox("Bio-E Notes / Traits")
        traits_form = QFormLayout(traits_box)
        self.ed_traits = QTextEdit()
        self.ed_traits.setPlaceholderText("One trait per line (or notes about Bio-E purchases)")
        traits_form.addRow("", self.ed_traits)
        bio_outer.addWidget(traits_box)
        bio_outer.addStretch(1)

        self.update_psionic_availability()
        self.recalc_bioe_spent()

        # ===================== Equipment tab =====================
        self.equipment_layout = self.make_scrollable_tab(self.tab_equipment)
        equip_layout = self.equipment_layout

        weapons_box = QGroupBox("Weapons")
        weapons_form = QFormLayout(weapons_box)
        self.weapon_combos = []
        self.weapon_cost_labels = []
        self.weapon_detail_boxes = []
        self.weapon_attack_buttons = []
        self.weapon_damage_buttons = []

        for i in range(5):
            row = QWidget()
            row_l = QVBoxLayout()
            row_l.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_l)

            top = QWidget()
            top_l = QHBoxLayout()
            top_l.setContentsMargins(0, 0, 0, 0)
            top.setLayout(top_l)

            cb = QComboBox()
            cb.addItem("Select a weapon", "")
            for w in sorted(WEAPONS_CATALOG, key=lambda x: x["name"]):
                cb.addItem(w["name"], w["name"])

            btn_attack = QPushButton("Roll To Hit")
            btn_attack.setEnabled(False)
            btn_attack.clicked.connect(lambda _=False, idx=i: self.on_weapon_roll_to_hit(idx))

            btn_dmg = QPushButton("Roll Damage")
            btn_dmg.setEnabled(False)
            btn_dmg.clicked.connect(lambda _=False, idx=i: self.on_weapon_roll_damage(idx))

            cost_lbl = QLabel("$0")
            cost_lbl.setMinimumWidth(90)

            top_l.addWidget(cb, 1)
            top_l.addWidget(btn_attack, 0)
            top_l.addWidget(btn_dmg, 0)
            top_l.addWidget(cost_lbl, 0)

            details = QTextEdit()
            details.setReadOnly(True)
            details.setMinimumHeight(55)

            row_l.addWidget(top)
            row_l.addWidget(details)

            cb.currentIndexChanged.connect(lambda _=False, idx=i: self.on_weapon_changed(idx))

            self.weapon_combos.append(cb)
            self.weapon_cost_labels.append(cost_lbl)
            self.weapon_detail_boxes.append(details)
            self.weapon_attack_buttons.append(btn_attack)
            self.weapon_damage_buttons.append(btn_dmg)

            weapons_form.addRow(f"Weapon {i+1}", row)

        equip_layout.addWidget(weapons_box)

        armor_box = QGroupBox("Armor")
        armor_form = QFormLayout(armor_box)

        armor_row = QWidget()
        armor_row_l = QHBoxLayout()
        armor_row_l.setContentsMargins(0, 0, 0, 0)
        armor_row.setLayout(armor_row_l)

        self.cb_armor = QComboBox()
        self.cb_armor.addItem("Select armor", "")
        for a in sorted(ARMOR_CATALOG, key=lambda x: x["name"]):
            self.cb_armor.addItem(a["name"], a["name"])
        self.cb_armor.currentIndexChanged.connect(self.on_armor_changed)

        self.lbl_armor_cost = QLabel("$0")
        self.lbl_armor_cost.setMinimumWidth(90)
        armor_row_l.addWidget(self.cb_armor, 1)
        armor_row_l.addWidget(self.lbl_armor_cost, 0)

        self.ed_armor_name = QLineEdit()
        self.sp_armor_ar = QSpinBox()
        self.sp_armor_ar.setRange(0, 99)
        self.sp_armor_sdc = QSpinBox()
        self.sp_armor_sdc.setRange(0, 100_000)

        armor_form.addRow("Armor Type", armor_row)
        armor_form.addRow("Armor (custom name)", self.ed_armor_name)
        armor_form.addRow("AR", self.sp_armor_ar)
        armor_form.addRow("Armor SDC", self.sp_armor_sdc)

        equip_layout.addWidget(armor_box)

        shield_box = QGroupBox("Shields")
        shield_form = QFormLayout(shield_box)

        shield_row = QWidget()
        shield_row_l = QHBoxLayout()
        shield_row_l.setContentsMargins(0, 0, 0, 0)
        shield_row.setLayout(shield_row_l)

        self.cb_shield = QComboBox()
        self.cb_shield.addItem("Select shield", "")
        for s in sorted(SHIELD_CATALOG, key=lambda x: x["name"]):
            self.cb_shield.addItem(s["name"], s["name"])
        self.cb_shield.currentIndexChanged.connect(self.on_shield_changed)

        self.lbl_shield_cost = QLabel("$0")
        self.lbl_shield_cost.setMinimumWidth(90)

        shield_row_l.addWidget(self.cb_shield, 1)
        shield_row_l.addWidget(self.lbl_shield_cost, 0)

        self.lbl_shield_parry = QLabel("Parry Bonus: —")
        self.lbl_shield_sdc = QLabel("SDC: —")
        self.ed_shield_notes = QLineEdit()
        self.ed_shield_notes.setPlaceholderText("Notes (optional)")

        shield_form.addRow("Shield Type", shield_row)
        shield_form.addRow("", self.lbl_shield_parry)
        shield_form.addRow("", self.lbl_shield_sdc)
        shield_form.addRow("Notes", self.ed_shield_notes)

        equip_layout.addWidget(shield_box)

        gear_box = QGroupBox("Gear")
        gear_form = QFormLayout(gear_box)
        self.gear_combos = []
        self.gear_cost_labels = []

        gear_sorted = sorted(GEAR_CATALOG, key=lambda x: x["name"])
        for i in range(30):
            row = QWidget()
            row_l = QHBoxLayout()
            row_l.setContentsMargins(0, 0, 0, 0)
            row.setLayout(row_l)

            cb = QComboBox()
            cb.addItem("Select gear item", "")
            for g in gear_sorted:
                cb.addItem(g["name"], g["name"])

            cost_lbl = QLabel("$0")
            cost_lbl.setMinimumWidth(90)

            row_l.addWidget(cb, 1)
            row_l.addWidget(cost_lbl, 0)

            cb.currentIndexChanged.connect(lambda _=False, idx=i: self.on_gear_changed(idx))

            self.gear_combos.append(cb)
            self.gear_cost_labels.append(cost_lbl)

            gear_form.addRow(f"Gear {i+1}", row)

        equip_layout.addWidget(gear_box)
        equip_layout.addStretch(1)

        # ===================== Vehicles tab =====================
        self.vehicles_layout = self.make_scrollable_tab(self.tab_vehicles)
        vehicles_layout = self.vehicles_layout
        self.vehicle_sections: dict[str, dict[str, Any]] = {}
        self._build_vehicle_section(vehicles_layout, "Landcraft", VEHICLES_LANDCRAFT, key="landcraft")
        self._build_vehicle_section(vehicles_layout, "Watercraft", VEHICLES_WATERCRAFT, key="watercraft")
        self._build_vehicle_section(vehicles_layout, "Aircraft", VEHICLES_AIRCRAFT, key="aircraft")
        vehicles_layout.addStretch(1)

        # Initialize dependent UI state
        self.on_animal_source_changed()
        self.recalc_combat_from_training()
        self.recalc_total_wealth()

    # ---------- Dice logging ----------

    def log_roll(self, text: str) -> None:
        self.roll_log.append(text)
        sb = self.roll_log.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())

    def roll_dice(self, count: int, sides: int) -> Tuple[List[int], int]:
        rolls = [random.randint(1, sides) for _ in range(count)]
        return rolls, sum(rolls)

    def eval_dice_expression(self, expr: str) -> Tuple[int, str]:
        raw = expr.strip()
        work = raw.replace(",", "")
        work = work.replace("×", "x")
        work = re.sub(r"\s+", " ", work).strip()
        work_math = (
            work.replace(" x ", " * ").replace(" X ", " * ").replace("x", "*")
            if " x " in work or " X " in work
            else work
        )

        roll_details: List[str] = []

        def repl(m: re.Match) -> str:
            num_str = m.group(1) or "1"
            die_str = m.group(2)
            n = int(num_str)
            sides = 100 if die_str == "%" else int(die_str)
            rolls, subtotal = self.roll_dice(n, sides)
            roll_details.append(f"rolling {n}d{sides}... {rolls} = {subtotal}")
            return str(subtotal)

        dice_re = re.compile(r"(\d*)\s*[dD]\s*(%|\d+)")
        replaced = dice_re.sub(repl, work_math)

        math_only = re.sub(r"[A-Za-z]+", "", replaced)
        math_only = math_only.replace('"', "").replace("’", "").replace("'", "")
        math_only = re.sub(r"\s+", " ", math_only).strip()

        if not re.fullmatch(r"[0-9+\-*/(). ]+", math_only):
            raise ValueError(f"Unsupported expression: {raw}")

        total = int(eval(math_only, {"__builtins__": {}}, {}))
        detail = f"{raw} -> " + " | ".join(roll_details)
        return total, detail

    def log_roll_expression(self, expr: str) -> int:
        total, detail = self.eval_dice_expression(expr)
        self.log_roll(f"{detail} Total = {total}")
        return total

    def on_roll_generic_die(self, faces: int) -> None:
        count = int(self.dice_counts[faces].value())
        if count <= 0:
            self.log_roll(f"(skipped) rolling {count}d{faces}")
            return
        rolls, total = self.roll_dice(count, faces)
        self.log_roll(f"rolling {count}d{faces}... {rolls} Total = {total}")
    
    def on_roll_hp_clicked(self) -> None:
        pe_val = self.get_effective_attribute("PE")
        roll = random.randint(1, 6)
        hp = pe_val + roll
        self.sp_hp.setValue(hp)
        self.log_roll(f"HP roll: effective PE({pe_val}) + 1d6({roll}) = {hp}")

    def on_skills_changed(self) -> None:
        self.recalc_skill_displays()
        self.recalc_combat_from_training()
        self.update_psionic_availability()
        self.recalc_bioe_spent()

    def on_roll_skill_check(self, cb: QComboBox, lookup: dict[str, dict[str, Any]]) -> None:
        """Roll 1d100 vs the current displayed/derived skill % (success = roll <= %)."""
        skill_name = self._selected_skill_name(cb)
        if not skill_name:
            self.log_roll("Skill roll: (no skill selected)")
            return

        pct = self._calc_skill_pct(skill_name, lookup)
        if pct is None:
            self.log_roll(f"Skill roll: {skill_name} (no % found) -> skipped")
            return

        roll = random.randint(1, 100)
        success = roll <= int(pct)

        self.log_roll(
            f"Skill roll: {skill_name} ({pct}%) 1d100={roll} -> {'SUCCESS' if success else 'FAIL'}"
        )



    # ---------- Settings ----------
    def on_toggle_dark_mode(self, enabled: bool) -> None:
        self.dark_mode_enabled = enabled

        app = QApplication.instance()
        if app is None:
            return

        icons_dir = r"C:\Users\ianrw\Desktop\TurtleCom\assets\icons"
        arrow_qss = build_arrow_icons_qss(icons_dir)

        # If you have a LIGHT_QSS, use it here. If not, just use "" for light mode.
        base_qss = DARK_QSS if enabled else ""

        app.setStyleSheet(base_qss + "\n" + arrow_qss)
    # ---------- Skill rules ----------
    def _load_skill_rules(self) -> None:
        rules_path = DATA_DIR / "rules" / "skills.json"
        if not rules_path.exists():
            QMessageBox.warning(self, "Missing skills.json", f"Could not find:\n\n{rules_path}")
            self.skill_rules = {"professional": {}, "amateur": {}}
            return
        try:
            with rules_path.open("r", encoding="utf-8") as f:
                self.skill_rules = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Skills Load Error", f"Could not read skills.json:\n\n{rules_path}\n\n{e}")
            self.skill_rules = {"professional": {}, "amateur": {}}

    def _build_skill_models(self) -> None:
        self.pro_model, self.pro_skill_lookup = self._make_grouped_model(self.skill_rules.get("professional", {}))
        self.amateur_model, self.amateur_skill_lookup = self._make_grouped_model(self.skill_rules.get("amateur", {}))

    def _make_grouped_model(self, grouped: dict[str, list[Any]]) -> tuple[QStandardItemModel, dict[str, dict[str, Any]]]:
        model = QStandardItemModel()
        lookup: dict[str, dict[str, Any]] = {}

        blank = QStandardItem("")
        blank.setData("", Qt.UserRole)
        model.appendRow(blank)

        for category, skills in grouped.items():
            header = QStandardItem(category)
            header.setFlags(Qt.ItemIsEnabled)
            header.setData(None, Qt.UserRole)
            model.appendRow(header)

            for s in skills:
                if not isinstance(s, dict):
                    continue
                name = s.get("name", "")
                if not isinstance(name, str) or not name.strip():
                    continue
                name = name.strip()

                item = QStandardItem(f"  {name}")
                item.setData(name, Qt.UserRole)
                model.appendRow(item)
                lookup[name] = s

            sep = QStandardItem("──────────")
            sep.setFlags(Qt.ItemIsEnabled)
            sep.setData(None, Qt.UserRole)
            model.appendRow(sep)

        return model, lookup

    def _selected_skill_name(self, cb: QComboBox) -> str:
        name = cb.currentData(Qt.UserRole)
        return name if isinstance(name, str) else ""

    def _calc_skill_pct(self, skill_name: str, lookup: dict[str, dict[str, Any]]) -> Optional[int]:
        if not skill_name:
            return None

        rule = lookup.get(skill_name)
        if not isinstance(rule, dict):
            return None

        base = rule.get("base_pct")
        if isinstance(base, list) and base:
            base_val = base[0]
        elif isinstance(base, int):
            base_val = base
        else:
            return None

        default_per_level = int(self.skill_rules.get("meta", {}).get("default_per_level", 5))
        per_level = rule.get("per_level", None)
        if not isinstance(per_level, int) or per_level <= 0:
            per_level = default_per_level

        level = int(self.sp_level.value())

        attrib_name = rule.get("attribute")
        attrib_score = self.get_effective_attribute(attrib_name) if attrib_name in self.attribute_fields else 0

        mode = self.skill_rules.get("attribute_bonus_mode", "simple")
        attrib_mod = _simple_attribute_mod(attrib_score) if mode == "simple" and attrib_score > 0 else 0

        physical_totals = self._get_physical_skill_totals()
        extra_pct = int(physical_totals["skill_pct_bonus"].get(skill_name, 0))

        return base_val + per_level * max(0, (level - 1)) + attrib_mod + extra_pct

    def recalc_skill_displays(self) -> None:
        for cb, lbl in zip(self.pro_skill_boxes, self.pro_skill_pct_labels):
            name = self._selected_skill_name(cb)
            pct = self._calc_skill_pct(name, self.pro_skill_lookup)
            lbl.setText(f"{pct}%" if pct is not None else "—")

        for cb, lbl in zip(self.amateur_skill_boxes, self.amateur_skill_pct_labels):
            name = self._selected_skill_name(cb)
            pct = self._calc_skill_pct(name, self.amateur_skill_lookup)
            lbl.setText(f"{pct}%" if pct is not None else "—")

    # ---------- Attributes rolling ----------
    def roll_attribute_score(self) -> tuple[int, list[int]]:
        rolls = [random.randint(1, 6) for _ in range(3)]
        total = sum(rolls)
        if total in (16, 17, 18):
            extra = random.randint(1, 6)
            rolls.append(extra)
            total += extra
        return total, rolls

    def on_roll_single_attribute(self, attr_name: str) -> None:
        sp = self.attribute_fields.get(attr_name)
        if sp is None:
            return
        total, rolls = self.roll_attribute_score()
        sp.setValue(total)
        self.log_roll(f"Attribute {attr_name}: rolled {rolls} => {total}")

    def on_roll_all_attributes(self) -> None:
        for attr_name in ("IQ", "ME", "MA", "PS", "PP", "PE", "PB", "Speed"):
            self.on_roll_single_attribute(attr_name)
        self.statusBar().showMessage("Rolled all attributes")

    # ---------- Animal Source / Type / Animal ----------
    def on_animal_source_changed(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")

        self.cb_animal_type.blockSignals(True)
        self.cb_animal.blockSignals(True)
        try:
            self.cb_animal_type.clear()
            self.cb_animal.clear()

            self.cb_animal_type.addItem("Roll or select your animal type", "")
            self.cb_animal.addItem("Roll or select your animal", "")

            if source == "tmntos":
                for _, tname in TMNTOS_ANIMAL_TYPE_RANGES:
                    self.cb_animal_type.addItem(tname, tname)
                self.btn_roll_animal_type.setEnabled(True)
                self.btn_roll_animal.setEnabled(True)
            else:
                self.btn_roll_animal_type.setEnabled(False)
                self.btn_roll_animal.setEnabled(False)
        finally:
            self.cb_animal_type.blockSignals(False)
            self.cb_animal.blockSignals(False)

    def on_animal_type_changed(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")
        animal_type = str(self.cb_animal_type.currentData() or "")

        self.cb_animal.blockSignals(True)
        try:
            self.cb_animal.clear()
            self.cb_animal.addItem("Roll or select your animal", "")

            if source == "tmntos":
                table = TMNTOS_ANIMALS_BY_TYPE.get(animal_type, [])
                for _, aname in table:
                    self.cb_animal.addItem(aname, aname)
        finally:
            self.cb_animal.blockSignals(False)

    def on_roll_animal_type(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")
        if source != "tmntos":
            return

        roll = _roll_d100()
        chosen = _pick_from_ranges(TMNTOS_ANIMAL_TYPE_RANGES, roll)
        if not chosen:
            return
        idx = self.cb_animal_type.findData(chosen)
        self.cb_animal_type.setCurrentIndex(idx if idx != -1 else 0)
        self.log_roll(f"Animal Type (TMNTOS): rolled d100={roll} => {chosen}")

    def on_roll_animal(self) -> None:
        source = str(self.cb_animal_source.currentData() or "")
        animal_type = str(self.cb_animal_type.currentData() or "")

        if source != "tmntos":
            return

        table = TMNTOS_ANIMALS_BY_TYPE.get(animal_type, [])
        if not table:
            return
        roll = _roll_d100()
        chosen = _pick_from_ranges(table, roll)
        if not chosen:
            return
        idx = self.cb_animal.findData(chosen)
        self.cb_animal.setCurrentIndex(idx if idx != -1 else 0)
        self.log_roll(f"Animal (TMNTOS / {animal_type}): rolled d100={roll} => {chosen}")

    # ---------- Combat training ----------
    def on_toggle_combat_override(self, enabled: bool) -> None:
        self._set_combat_spinboxes_editable(bool(enabled))
        self.recalc_combat_from_training()

    def _set_combat_spinboxes_editable(self, editable: bool) -> None:
        for sp in (self.sp_strike, self.sp_parry, self.sp_dodge, self.sp_initiative, self.sp_actions):
            sp.setReadOnly(not editable)
            sp.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows if editable else QSpinBox.ButtonSymbols.NoButtons)

    def _calc_training_summary(self, training_name: str, level: int) -> dict[str, Any]:
        out: dict[str, Any] = {
            "strike": 0,
            "parry": 0,
            "dodge": 0,
            "initiative": 0,
            "actions_per_round": int(BASELINE_COMBAT["actions_per_round"]),
            "unarmed_damage": str(BASELINE_COMBAT["unarmed_damage"]),
            "known_actions": list(BASELINE_COMBAT["known_actions"]),
            "known_reactions": list(BASELINE_COMBAT["known_reactions"]),
            "critical_range": tuple(BASELINE_COMBAT["critical_range"]),
            "roll_with_impact": 0,
            "melee_damage_list": [],
            "melee_damage": "—",
            "specials": [],
            "notes": list(BASELINE_COMBAT.get("notes", [])),
        }

        if training_name == "None":
            return out

        table = COMBAT_TRAINING_RULES.get(training_name, {})
        for lvl in sorted(table.keys()):
            if lvl > level:
                break
            delta = table[lvl]

            for k in ("strike", "parry", "dodge", "initiative", "actions_per_round"):
                if k in delta and isinstance(delta[k], int):
                    out[k] += int(delta[k])

            if "roll_with_impact" in delta and isinstance(delta["roll_with_impact"], int):
                out["roll_with_impact"] += int(delta["roll_with_impact"])

            if "melee_damage" in delta and isinstance(delta["melee_damage"], str):
                out["melee_damage_list"].append(delta["melee_damage"])

            if "unlock_actions" in delta and isinstance(delta["unlock_actions"], list):
                for a in delta["unlock_actions"]:
                    if isinstance(a, str) and a and a not in out["known_actions"]:
                        out["known_actions"].append(a)

            if "unlock_reactions" in delta and isinstance(delta["unlock_reactions"], list):
                for r in delta["unlock_reactions"]:
                    if isinstance(r, str) and r and r not in out["known_reactions"]:
                        out["known_reactions"].append(r)

            if "critical_range" in delta and isinstance(delta["critical_range"], tuple) and len(delta["critical_range"]) == 2:
                out["critical_range"] = delta["critical_range"]

            if "specials" in delta and isinstance(delta["specials"], list):
                for s in delta["specials"]:
                    if isinstance(s, str) and s:
                        out["specials"].append(s)

        out["melee_damage"] = _combine_melee_damage(out["melee_damage_list"])
        return out

    def recalc_combat_from_training(self) -> None:
        training = self.cb_combat_training.currentData()
        training_name = str(training) if isinstance(training, str) and training else "None"
        level = int(self.sp_level.value())

        summary = self._calc_training_summary(training_name, level)
        physical = self._get_physical_skill_totals()
        override_on = bool(self.chk_combat_override.isChecked())

        derived_strike = int(summary["strike"]) + int(physical["combat"].get("strike", 0))
        derived_parry = int(summary["parry"]) + int(physical["combat"].get("parry", 0))
        derived_dodge = int(summary["dodge"]) + int(physical["combat"].get("dodge", 0))
        derived_initiative = int(summary["initiative"]) + int(physical["combat"].get("initiative", 0))
        derived_actions = int(summary["actions_per_round"]) + int(physical["combat"].get("actions_per_round", 0))
        derived_roll_with_impact = int(summary.get("roll_with_impact", 0)) + int(physical["combat"].get("roll_with_impact", 0))

        extra_attacks = list(summary.get("known_actions", []))
        for attack_name in physical.get("extra_attacks", []):
            if attack_name not in extra_attacks:
                extra_attacks.append(attack_name)

        if hasattr(self, "lw_combat_techniques"):
            self.lw_combat_techniques.clear()
            for attack_name in extra_attacks:
                self.lw_combat_techniques.addItem(attack_name)

        if not override_on:
            self.sp_strike.blockSignals(True)
            self.sp_parry.blockSignals(True)
            self.sp_dodge.blockSignals(True)
            self.sp_initiative.blockSignals(True)
            self.sp_actions.blockSignals(True)
            try:
                self.sp_strike.setValue(derived_strike)
                self.sp_parry.setValue(derived_parry)
                self.sp_dodge.setValue(derived_dodge)
                self.sp_initiative.setValue(derived_initiative)
                self.sp_actions.setValue(derived_actions)
            finally:
                self.sp_strike.blockSignals(False)
                self.sp_parry.blockSignals(False)
                self.sp_dodge.blockSignals(False)
                self.sp_initiative.blockSignals(False)
                self.sp_actions.blockSignals(False)

        if not self.chk_combat_auto_details.isChecked():
            return

        crit_min, crit_max = summary["critical_range"]
        crit_text = f"{crit_min}" if crit_min == crit_max else f"{crit_min}–{crit_max}"

        lines: list[str] = []
        lines.append(f"Training: {training_name}")
        lines.append(f"Level: {level}")
        if override_on:
            lines.append("NOTE: Override enabled — numeric fields are manual.")
        lines.append("")
        lines.append("Derived (training + physical skills):")
        lines.append(f"• Strike: {derived_strike:+d}")
        lines.append(f"• Parry: {derived_parry:+d}")
        lines.append(f"• Dodge: {derived_dodge:+d}")
        lines.append(f"• Initiative: {derived_initiative:+d}")
        lines.append(f"• Actions/round: {derived_actions}")
        lines.append(f"• Roll with Impact bonus: +{derived_roll_with_impact}")
        lines.append(f"• Critical range: {crit_text}")

        sword_strike = int(physical["combat"].get("strike_swords", 0))
        sword_parry = int(physical["combat"].get("parry_swords", 0))
        sword_damage = int(physical["combat"].get("damage_swords", 0))
        pull_punch = int(physical["combat"].get("pull_punch", 0))

        if sword_strike or sword_parry or sword_damage:
            lines.append("")
            lines.append("Weapon-specific bonuses:")
            lines.append(f"• Sword Strike bonus: {sword_strike:+d}")
            lines.append(f"• Sword Parry bonus: {sword_parry:+d}")
            lines.append(f"• Sword Damage bonus: {sword_damage:+d}")

        if pull_punch:
            lines.append(f"• Pull Punch bonus: {pull_punch:+d}")

        if summary.get("melee_damage", "—") != "—":
            lines.append(f"• Melee damage bonus: {summary['melee_damage']}")

        if physical.get("notes"):
            lines.append("")
            lines.append("Physical skill notes:")
            for note in physical["notes"]:
                lines.append(f"• {note}")

        self.ed_combat_training_details.setPlainText("\n".join(lines))
    # ---------------- Size Roll + Apply ----------------
    def on_roll_size_clicked(self) -> None:
        try:
            size_level = int(self.cb_size_level.currentData())
            build_key = str(self.cb_size_build.currentData())
            if size_level not in SIZE_LEVEL_FORMULAS:
                QMessageBox.warning(self, "Size", "Invalid size selection.")
                return

            formulas = SIZE_LEVEL_FORMULAS[size_level]
            weight_expr = formulas["weight"]
            height_expr = formulas[build_key]

            weight_total = self.log_roll_expression(weight_expr.replace("D%", "D%"))
            height_total = self.log_roll_expression(height_expr.replace("D%", "D%"))

            if "ounce" in weight_expr.lower():
                self.ed_weight.setText(f"{weight_total} oz")
            else:
                self.ed_weight.setText(f"{weight_total} lbs")

            self.ed_height.setText(self.format_inches(height_total))

            effects = SIZE_LEVEL_EFFECTS.get(size_level, {})
            self.apply_size_effects(effects)

            self.statusBar().showMessage(f"Rolled size {size_level} ({build_key.title()})")
        except Exception as e:
            QMessageBox.critical(self, "Roll failed", f"Could not roll/apply size.\n\n{e}")

    def format_inches(self, total_inches: int) -> str:
        if total_inches < 12:
            return f'{total_inches}"'
        feet = total_inches // 12
        inches = total_inches % 12
        return f"{feet}' {inches}\""

    def apply_size_effects(self, effects: dict[str, int]) -> None:
        for attr in ["IQ", "PS", "PE", "Speed"]:
            if attr in effects and attr in self.attribute_fields:
                base = int(self.attribute_fields[attr].value())
                self.attribute_fields[attr].setValue(max(0, base + int(effects[attr])))

        if "SDC" in effects:
            self.sp_sdc.setValue(max(0, int(effects["SDC"])))

        if "bio_e" in effects:
            self.sp_bio_total.setValue(max(0, int(self.sp_bio_total.value()) + int(effects["bio_e"])))

        parts = []
        for k, v in effects.items():
            sign = "+" if v >= 0 else ""
            parts.append(f"{k} {sign}{v}")
        self.log_roll("Applied size effects: " + ", ".join(parts))

    # ---------- Weapon rolling ----------
    def _weapon_damage_expr(self, weapon_name: str) -> Optional[str]:
        w = WEAPONS_BY_NAME.get(weapon_name)
        if not w:
            return None
        details = str(w.get("details", ""))

        m = re.search(r"Damage\s+([0-9Dd%+\-– ]+)", details)
        if not m:
            return None

        raw = m.group(1).strip()
        raw = raw.replace(" ", "")
        raw = raw.replace("D", "d").replace("d%", "d%")

        # Prefer the first entry in ranges like 2D6–3D6 or "2D6–3D6"
        raw = raw.replace("–", "-")
        if "-" in raw and "d" in raw:
            left = raw.split("-", 1)[0]
            if re.fullmatch(r"\d+d\d+(?:\+\d+)?", left):
                return left

        # Simple "1d8+2" etc
        if re.fullmatch(r"\d+d\d+(?:\+\d+)?", raw):
            return raw

        # Sometimes "6D6–7D6" already handled above, or "6D6to12D6"
        m2 = re.search(r"(\d+d\d+(?:\+\d+)?)", raw)
        return m2.group(1) if m2 else None

    def _melee_damage_bonus_int(self) -> int:
        training = str(self.cb_combat_training.currentData() or "None")
        level = int(self.sp_level.value())
        summary = self._calc_training_summary(training, level)
        bonus = 0
        for s in summary.get("melee_damage_list", []) or []:
            if isinstance(s, str):
                m = re.search(r"([+-]\d+)", s.replace(" ", ""))
                if m:
                    bonus += int(m.group(1))
        return bonus

    def on_weapon_roll_to_hit(self, idx: int) -> None:
        if idx >= len(self.weapon_combos):
            return
        weapon = str(self.weapon_combos[idx].currentData() or "")
        if not weapon:
            return
        d20 = random.randint(1, 20)
        bonus = int(self.sp_strike.value())
        total = d20 + bonus
        self.log_roll(f"[To Hit] {weapon}: d20={d20} + Strike({bonus:+d}) => {total}")

    def on_weapon_roll_damage(self, idx: int) -> None:
        if idx >= len(self.weapon_combos):
            return
        weapon = str(self.weapon_combos[idx].currentData() or "")
        if not weapon:
            return

        expr = self._weapon_damage_expr(weapon)
        if not expr:
            self.log_roll(f"[Damage] {weapon}: (no damage expression found)")
            return

        base_total, detail = self.eval_dice_expression(expr)
        dmg_bonus = self._melee_damage_bonus_int()
        total = base_total + dmg_bonus
        self.log_roll(f"[Damage] {weapon}: {detail} Base={base_total} + MeleeBonus({dmg_bonus:+d}) => {total}")

    # ---------- Equipment handlers ----------
    def on_weapon_changed(self, idx: int) -> None:
        if idx >= len(self.weapon_combos):
            return
        name = str(self.weapon_combos[idx].currentData() or "")
        if not name:
            self.weapon_cost_labels[idx].setText("$0")
            self.weapon_detail_boxes[idx].setPlainText("")
            self.weapon_attack_buttons[idx].setEnabled(False)
            self.weapon_damage_buttons[idx].setEnabled(False)
            self.recalc_total_wealth()
            self.recalc_weight_breakdown()
            return
        w = WEAPONS_BY_NAME.get(name, {})
        self.weapon_cost_labels[idx].setText(str(w.get("cost", "$0")))
        self.weapon_detail_boxes[idx].setPlainText(str(w.get("details", "")))
        self.weapon_attack_buttons[idx].setEnabled(True)
        self.weapon_damage_buttons[idx].setEnabled(True)
        self.recalc_total_wealth()
        self.recalc_weight_breakdown()

    def on_armor_changed(self) -> None:
        name = str(self.cb_armor.currentData() or self.cb_armor.currentText() or "").strip()

        if not name:
            self.lbl_armor_cost.setText("$0")
            self.sp_armor_ar.setValue(0)
            self.sp_armor_sdc.setValue(0)
            self.recalc_total_wealth()
            self.recalc_weight_breakdown()
            return

        armor = ARMOR_BY_NAME.get(name, {})
        self.lbl_armor_cost.setText(str(armor.get("cost", "$0")))

        ar = armor.get("ar")
        sdc = armor.get("sdc")

        self.sp_armor_ar.setValue(int(ar) if isinstance(ar, int) else 0)
        self.sp_armor_sdc.setValue(int(sdc) if isinstance(sdc, int) else 0)

        self.sync_defense_summary_fields()
        self.recalc_total_wealth()
        self.recalc_weight_breakdown()

    def on_shield_changed(self) -> None:
        name = str(self.cb_shield.currentData() or self.cb_shield.currentText() or "").strip()

        if not name:
            self.lbl_shield_cost.setText("$0")
            self.lbl_shield_parry.setText("Parry Bonus: —")
            self.lbl_shield_sdc.setText("SDC: —")
            self.sync_defense_summary_fields()
            self.recalc_total_wealth()
            self.recalc_weight_breakdown()
            return

        shield = SHIELD_BY_NAME.get(name, {})

        self.lbl_shield_cost.setText(str(shield.get("cost", "$0")))

        parry = shield.get("parry")
        sdc = shield.get("sdc")

        self.lbl_shield_parry.setText(
            f"Parry Bonus: {parry:+d}" if isinstance(parry, int) else "Parry Bonus: —"
        )
        self.lbl_shield_sdc.setText(
            f"SDC: {sdc}" if isinstance(sdc, int) else "SDC: —"
        )

        self.sync_defense_summary_fields()
        self.recalc_total_wealth()
        self.recalc_weight_breakdown()

    def on_gear_changed(self, idx: int) -> None:
        if idx >= len(self.gear_combos):
            return
        name = str(self.gear_combos[idx].currentData() or "")
        if not name:
            self.gear_cost_labels[idx].setText("$0")
            self.recalc_total_wealth()
            self.recalc_weight_breakdown()
            return
        g = GEAR_BY_NAME.get(name, {})
        self.gear_cost_labels[idx].setText(str(g.get("cost", "$0")))
        self.recalc_total_wealth()
        self.recalc_weight_breakdown()

# ---------- Bio-E helpers ----------

    
    def _bioe_resolve_key(self, animal_label_or_key: str) -> str:
        """
        Takes whatever your UI has (e.g. 'Dog', 'Black Bear', or already a BIOE key)
        and returns a valid BIOE_ANIMAL_DATA key when possible.
        """
        if not animal_label_or_key:
            return ""

        # If it already matches a BIOE key, keep it
        if animal_label_or_key in BIOE_ANIMAL_DATA:
            return animal_label_or_key

        norm = _norm_animal_label(animal_label_or_key)
        key = BIOE_ANIMAL_ALIASES.get(norm, "")

        # Some UI strings are descriptive like "Crocodile (or Alligator)" – try substring matching
        if not key:
            for alias_norm, bioe_key in BIOE_ANIMAL_ALIASES.items():
                if alias_norm and alias_norm in norm:
                    key = bioe_key
                    break

        return key

    def _bioe_get_animal_rule(self, animal: str) -> dict[str, Any]:
        """
        Takes whatever the UI selected (e.g. 'Dog', 'Black Bear', etc.)
        and resolves it to a valid BIOE_ANIMAL_DATA key.
        """

        if not animal:
            return dict(BIOE_DEFAULT_ANIMAL)

        # If it's already a real key, use it directly
        if animal in BIOE_ANIMAL_DATA:
            return dict(BIOE_ANIMAL_DATA[animal])

        norm = animal.strip().upper()

        # Try alias lookup
        key = BIOE_ANIMAL_ALIASES.get(norm)

        if key and key in BIOE_ANIMAL_DATA:
            return dict(BIOE_ANIMAL_DATA[key])

        # Try partial match fallback
        for alias, bioe_key in BIOE_ANIMAL_ALIASES.items():
            if alias in norm and bioe_key in BIOE_ANIMAL_DATA:
                return dict(BIOE_ANIMAL_DATA[bioe_key])

        # Nothing matched
        return dict(BIOE_DEFAULT_ANIMAL)

    def _bioe_combo_cost(self, cb: QComboBox) -> int:
        val = cb.currentData()
        return int(val) if isinstance(val, int) else 0

    def _bioe_set_original_fields(self, original: dict[str, Any]) -> None:
        size_level = original.get("size_level", "")
        length_in = original.get("length_in", "")
        weight_lbs = original.get("weight_lbs", "")
        build = original.get("build", "")

        self.ed_bio_orig_size_level.setText(str(size_level) if size_level != "" else "")
        self.ed_bio_orig_length.setText(self.format_inches(int(length_in)) if isinstance(length_in, int) else str(length_in))
        self.ed_bio_orig_weight.setText(f"{weight_lbs} lbs" if isinstance(weight_lbs, int) else str(weight_lbs))
        self.ed_bio_orig_build.setText(str(build))

        # Set mutant size selector to original by default (if possible)
        if isinstance(size_level, int) and 1 <= size_level <= 20:
            idx = self.cb_bio_mutant_size_level.findData(size_level)
            self.cb_bio_mutant_size_level.setCurrentIndex(idx if idx != -1 else 0)

    def _bioe_populate_natural_weapons(self, items: list[dict[str, Any]]) -> None:
        # Populate each combo with None + all weapons
        for i, cb in enumerate(getattr(self, "bio_weapon_combos", [])):
            cb.blockSignals(True)
            try:
                cb.clear()
                cb.addItem("None", None)
                for it in items:
                    name = str(it.get("name", "")).strip()
                    cost = it.get("cost", 0)
                    if name:
                        cb.addItem(name, it)  # store dict
                cb.setCurrentIndex(0)
            finally:
                cb.blockSignals(False)

            # Clear details
            if i < len(self.bio_weapon_cost_labels):
                self.bio_weapon_cost_labels[i].setText("0")
            if i < len(self.bio_weapon_detail_boxes):
                self.bio_weapon_detail_boxes[i].setPlainText("")

    def _bioe_populate_abilities(self, items: list[dict[str, Any]]) -> None:
        for i, cb in enumerate(getattr(self, "bio_ability_combos", [])):
            cb.blockSignals(True)
            try:
                cb.clear()
                cb.addItem("None", None)
                for it in items:
                    name = str(it.get("name", "")).strip()
                    if name:
                        cb.addItem(name, it)  # store dict
                cb.setCurrentIndex(0)
            finally:
                cb.blockSignals(False)

            if i < len(self.bio_ability_cost_labels):
                self.bio_ability_cost_labels[i].setText("0")
            if i < len(self.bio_ability_detail_boxes):
                self.bio_ability_detail_boxes[i].setPlainText("")

    def update_psionic_availability(self) -> None:
        me = int(self.attribute_fields.get("ME", QSpinBox()).value()) if "ME" in self.attribute_fields else 0
        allowed = me >= 12
        for cb in getattr(self, "bio_psionic_combos", []):
            cb.setEnabled(allowed)
            if not allowed:
                cb.setCurrentIndex(0)  # None

        # If you want, show a hint in remaining label via styling
        if hasattr(self, "lbl_bio_remaining"):
            if allowed:
                self.lbl_bio_remaining.setToolTip("")
            else:
                self.lbl_bio_remaining.setToolTip("ME must be 12+ to select Psionic Powers.")

        self.recalc_bioe_spent()

    def on_bioe_animal_selected(self) -> None:
        # Called when animal changes on Basics tab
        animal = str(self.cb_animal.currentData() or "")
        rule = self._bioe_get_animal_rule(animal)

        # Set total Bio-E to animal starting Bio-E (this does NOT include size effects you add elsewhere)
        # If you want size-based Bio-E to stack, keep your size logic that modifies sp_bio_total;
        # but that can fight with this setter. For now: overwrite with animal base, then recalc spent.
        self.sp_bio_total.setValue(int(rule.get("bio_e", 0) or 0))

        self._bioe_set_original_fields(rule.get("original", {}) if isinstance(rule.get("original"), dict) else {})

        self.ed_bio_mutant_changes.setPlainText(str(rule.get("mutant_changes_text", "") or ""))

        # Attribute bonus summary
        bonuses = rule.get("attribute_bonuses", {})
        if isinstance(bonuses, dict) and bonuses:
            parts = []
            for k, v in bonuses.items():
                if isinstance(v, int):
                    sign = "+" if v >= 0 else ""
                    parts.append(f"{k} {sign}{v}")
            self.ed_bio_attr_bonus.setPlainText(", ".join(parts) if parts else "—")
        else:
            self.ed_bio_attr_bonus.setPlainText("—")

        self._bioe_populate_natural_weapons(rule.get("natural_weapons", []) if isinstance(rule.get("natural_weapons"), list) else [])
        self._bioe_populate_abilities(rule.get("abilities", []) if isinstance(rule.get("abilities"), list) else [])

        # Reset human features to None
        for cb in (self.cb_human_hands, self.cb_human_biped, self.cb_human_speech, self.cb_human_looks):
            cb.setCurrentIndex(0)

        # Reset psionics
        for cb in getattr(self, "bio_psionic_combos", []):
            cb.setCurrentIndex(0)

        self.update_psionic_availability()
        self.recalc_bioe_spent()

    def _bioe_size_level_cost(self) -> int:
        # Placeholder: 5 Bio-E per step from original size level
        try:
            orig = int(self.ed_bio_orig_size_level.text().strip() or "0")
        except Exception:
            orig = 0
        try:
            chosen = int(self.cb_bio_mutant_size_level.currentData() or 0)
        except Exception:
            chosen = 0
        if orig <= 0 or chosen <= 0:
            return 0
        return abs(chosen - orig) * 5

    def recalc_bioe_spent(self) -> None:
        total_bio_e = int(self.sp_bio_total.value())

        animal_name = str(self.cb_animal.currentData() or self.cb_animal.currentText() or "")
        rule = self._bioe_get_animal_rule(animal_name)

        original = rule.get("original", {}) if isinstance(rule, dict) else {}
        original_size = original.get("size_level", None)

        selected_size = self.cb_bio_mutant_size_level.currentData()
        try:
            selected_size_int = int(selected_size)
        except (TypeError, ValueError):
            selected_size_int = None

        size_cost = 0
        if isinstance(original_size, int) and isinstance(selected_size_int, int):
            size_diff = selected_size_int - original_size
            size_cost = size_diff * 5
        self.lbl_bio_size_cost.setText(f"Cost: {size_cost:+d}")

        spent = 0

        for cb in (
            self.cb_human_hands,
            self.cb_human_biped,
            self.cb_human_speech,
            self.cb_human_looks,
        ):
            value = cb.currentData()
            if isinstance(value, int):
                spent += value

        spent += size_cost

        for cb, lbl, details in zip(
            self.bio_weapon_combos,
            self.bio_weapon_cost_labels,
            self.bio_weapon_detail_boxes,
        ):
            item = cb.currentData()
            if isinstance(item, dict):
                cost = int(item.get("cost", 0) or 0)
                spent += cost
                lbl.setText(str(cost))
                details.setPlainText(str(item.get("details", "")))
            else:
                lbl.setText("0")
                details.setPlainText("")

        for cb, lbl, details in zip(
            self.bio_ability_combos,
            self.bio_ability_cost_labels,
            self.bio_ability_detail_boxes,
        ):
            item = cb.currentData()
            if isinstance(item, dict):
                cost = int(item.get("cost", 0) or 0)
                spent += cost
                lbl.setText(str(cost))
                details.setPlainText(str(item.get("details", "")))
            else:
                lbl.setText("0")
                details.setPlainText("")

        me_value = int(self.attribute_fields.get("ME", QSpinBox()).value()) if "ME" in self.attribute_fields else 0
        psionics_allowed = me_value >= 12

        for cb, lbl in zip(self.bio_psionic_combos, self.bio_psionic_cost_labels):
            cost = cb.currentData()
            if not psionics_allowed:
                lbl.setText("0")
                continue
            if isinstance(cost, int):
                spent += cost
                lbl.setText(str(cost))
            else:
                lbl.setText("0")

        self.sp_bio_spent.blockSignals(True)
        self.sp_bio_spent.setValue(spent)
        self.sp_bio_spent.blockSignals(False)

        remaining = total_bio_e - spent
        self.lbl_bio_remaining.setText(f"Remaining: {remaining}")




    # ---------- Total Wealth ----------
    def recalc_total_wealth(self) -> None:
        credits = int(self.sp_total_credits.value())
        equip_cost = 0

        for cb in getattr(self, "weapon_combos", []):
            name = str(cb.currentData() or "")
            if name:
                equip_cost += _cost_to_int(str(WEAPONS_BY_NAME.get(name, {}).get("cost", "")))

        armor_type = str(getattr(self, "cb_armor", QComboBox()).currentData() or "")
        if armor_type:
            equip_cost += _cost_to_int(str(ARMOR_BY_NAME.get(armor_type, {}).get("cost", "")))

        shield_type = str(getattr(self, "cb_shield", QComboBox()).currentData() or "")
        if shield_type:
            equip_cost += _cost_to_int(str(SHIELD_BY_NAME.get(shield_type, {}).get("cost", "")))

        for cb in getattr(self, "gear_combos", []):
            name = str(cb.currentData() or "")
            if name:
                equip_cost += _cost_to_int(str(GEAR_BY_NAME.get(name, {}).get("cost", "")))

        vehicle_cost = 0
        for key in ("landcraft", "watercraft", "aircraft"):
            section = getattr(self, "vehicle_sections", {}).get(key, {})
            combos: list[QComboBox] = section.get("combos", [])
            for cb in combos:
                name = str(cb.currentData() or "")
                if name:
                    vehicle_cost += _cost_to_int(str(VEHICLES_LOOKUP.get(name, {}).get("cost", "")))

        total = credits + equip_cost + vehicle_cost
        self.ed_total_wealth.setText(f"{total}")
        
    # ---------- Vehicles UI ----------
    def _build_vehicle_section(self, parent_layout: QVBoxLayout, title: str, vehicles: list[dict[str, str]], key: str) -> None:
        box = QGroupBox(title)
        form = QFormLayout(box)

        combos: list[QComboBox] = []
        descs: list[QTextEdit] = []

        for idx in range(2):
            cb = QComboBox()
            cb.addItem("Select a vehicle", "")
            for v in vehicles:
                cb.addItem(v["name"], v["name"])

            desc = QTextEdit()
            desc.setReadOnly(True)
            desc.setMinimumHeight(70)

            cb.currentIndexChanged.connect(lambda _=False, k=key, i=idx: self.on_vehicle_changed(k, i))

            combos.append(cb)
            descs.append(desc)

            form.addRow(f"{title} {idx+1}", cb)
            form.addRow("Details", desc)

        parent_layout.addWidget(box)
        self.vehicle_sections[key] = {"combos": combos, "descs": descs}

    def on_vehicle_changed(self, section_key: str, idx: int) -> None:
        section = self.vehicle_sections.get(section_key, {})
        combos: list[QComboBox] = section.get("combos", [])
        descs: list[QTextEdit] = section.get("descs", [])
        if idx >= len(combos) or idx >= len(descs):
            return

        name = str(combos[idx].currentData() or "")
        if not name:
            descs[idx].setPlainText("")
            self.recalc_total_wealth()
            return

        v = VEHICLES_LOOKUP.get(name)
        if not v:
            descs[idx].setPlainText("")
            self.recalc_total_wealth()
            return

        text = (
            f"{v['name']}\n"
            f"Range: {v['range']}\n"
            f"Top Speed: {v['top_speed']}\n"
            f"SDC: {v['sdc']}\n"
            f"Cost: {v['cost']}\n"
        )
        descs[idx].setPlainText(text)
        self.recalc_total_wealth()


    def _parse_weight_lbs_from_text(self, text: str) -> float:
        """
        Extracts weights from text like:
        - "...; 2.0kg"
        - "10 lbs"
        Sums all found weights. Ignores dice-formulas like "300+6D10 lbs".
        """
        if not text:
            return 0.0

        total_lbs = 0.0

        # --- kg like "2.0kg" or "2 kg"
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*kg\b", text, flags=re.IGNORECASE):
            kg = float(m.group(1))
            total_lbs += kg * 2.2046226218

        # --- lbs like "10 lbs" or "10 lb"
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*lb(?:s)?\b", text, flags=re.IGNORECASE):
            lbs = float(m.group(1))
            total_lbs += lbs

        return total_lbs


    def _get_body_weight_lbs(self) -> float:
        """
        Reads body weight from self.ed_weight.
        Accepts:
        - "180" (assumed lbs)
        - "180 lbs"
        - "82 kg"
        """
        if not hasattr(self, "ed_weight"):
            return 0.0

        raw = (self.ed_weight.text() or "").strip()
        if not raw:
            return 0.0

        # pull first number
        m = re.search(r"(\d+(?:\.\d+)?)", raw)
        if not m:
            return 0.0

        val = float(m.group(1))
        if re.search(r"\bkg\b", raw, flags=re.IGNORECASE):
            return val * 2.2046226218

        # default lbs
        return val




    def _get_equipment_weight_lbs(self) -> float:
        """
        Sums weights we can detect from selected equipment:
        - weapons: WEAPONS_BY_NAME[name]['details'] contains 'kg'
        - shield: SHIELD_BY_NAME[name]['details'] contains 'lbs'
        - gear: currently most entries are not weighted (will count if details include kg/lbs)
        - armor: no weight in catalog currently (ignored unless you add it)
        """
        total = 0.0

        # weapons
        if hasattr(self, "weapon_combos"):
            for cb in self.weapon_combos:
                name = str(cb.currentData() or "")
                if not name:
                    continue
                w = WEAPONS_BY_NAME.get(name)
                if w:
                    total += self._parse_weight_lbs_from_text(str(w.get("details", "")))

        # shield
        if hasattr(self, "cb_shield"):
            sname = str(self.cb_shield.currentData() or "")
            if sname:
                s = SHIELD_BY_NAME.get(sname)
                if s:
                    total += self._parse_weight_lbs_from_text(str(s.get("details", "")))

        # gear (only counts if your details strings include kg/lbs)
        if hasattr(self, "gear_combos"):
            for cb in self.gear_combos:
                gname = str(cb.currentData() or "")
                if not gname:
                    continue
                g = GEAR_BY_NAME.get(gname)
                if g:
                    total += self._parse_weight_lbs_from_text(str(g.get("details", "")))

        # armor (ignored unless you later add weight data to ARMOR_CATALOG)
        return total


    def _get_vehicles_weight_lbs(self) -> float:
        """
        Vehicles catalog currently doesn't include weight in the text you print,
        so this will be 0 unless you add:
        v['weight'] = "2500 lbs" or "1200kg"
        """
        total = 0.0
        if not hasattr(self, "vehicle_sections"):
            return 0.0

        for key in ("landcraft", "watercraft", "aircraft"):
            section = self.vehicle_sections.get(key, {})
            combos = section.get("combos", [])
            for cb in combos:
                name = str(cb.currentData() or "")
                if not name:
                    continue
                v = VEHICLES_LOOKUP.get(name)
                if not v:
                    continue

                # Option A: you add v["weight"] later
                if "weight" in v and v["weight"]:
                    total += self._parse_weight_lbs_from_text(str(v["weight"]))
                    continue

                # Option B: if you later include "Weight: ..." in the desc text and want to parse it
                # (not used right now)
        return total


    def recalc_weight_breakdown(self) -> None:
        """
        Updates the read-only 'body + gear' weight field.
        """
        if not hasattr(self, "ed_weight_with_gear"):
            return

        body = self._get_body_weight_lbs()
        gear = self._get_equipment_weight_lbs()

        self.ed_weight_with_gear.setText(f"{body + gear:,.1f} lbs")

   

    # ---------------- Character IO ----------------
    def editor_to_character(self) -> Character:
        c = self.current_character

        c.name = self.ed_name.text().strip()

        animal_source = str(self.cb_animal_source.currentData() or "")
        animal_type = str(self.cb_animal_type.currentData() or "")
        animal = str(self.cb_animal.currentData() or "")

        c.animal = animal

        c.bio_e["animal_source"] = animal_source
        c.bio_e["animal_type"] = animal_type
        c.bio_e["animal"] = animal

        align = str(self.cb_alignment.currentData() or "")
        c.alignment = align

        c.age = self.ed_age.text().strip()
        c.gender = self.ed_gender.text().strip()

        c.weight = self.ed_weight.text().strip()
        c.height = self.ed_height.text().strip()
        c.size = f"{self.cb_size_level.currentData()} ({self.cb_size_build.currentText()})"

        try:
            setattr(c, "total_credits", int(self.sp_total_credits.value()))
            setattr(c, "total_wealth", int(self.ed_total_wealth.text() or "0"))
        except Exception:
            pass

        c.xp = int(self.sp_xp.value())
        c.level = int(self.sp_level.value())
        c.hit_points = int(self.sp_hp.value())
        c.sdc = int(self.sp_sdc.value())

        try:
            setattr(c, "weapons_selected", [str(cb.currentData() or "") for cb in self.weapon_combos])
            setattr(c, "armor_type", str(self.cb_armor.currentData() or self.cb_armor.currentText() or ""))
            setattr(c, "shield_type", str(self.cb_shield.currentData() or self.cb_shield.currentText() or ""))
            setattr(c, "shield_notes", self.ed_shield_notes.text().strip())
            setattr(c, "gear_selected", [str(cb.currentData() or "") for cb in self.gear_combos])
        except Exception:
            pass

        c.armor_name = self.ed_armor_name.text().strip()
        c.armor_ar = int(self.sp_armor_ar.value())
        c.armor_sdc = int(self.sp_armor_sdc.value())

        c.notes = self.ed_notes.toPlainText()

        for key, sp in self.attribute_fields.items():
            c.attributes[key] = int(sp.value())

        c.skills["pro"] = [self._selected_skill_name(cb) for cb in self.pro_skill_boxes]
        c.skills["amateur"] = [self._selected_skill_name(cb) for cb in self.amateur_skill_boxes]

        c.combat["training"] = str(self.cb_combat_training.currentData() or "None")
        c.combat["override"] = bool(self.chk_combat_override.isChecked())
        c.combat["auto_details"] = bool(self.chk_combat_auto_details.isChecked())
        c.combat["training_details_text"] = self.ed_combat_training_details.toPlainText()
        c.combat["strike"] = int(self.sp_strike.value())
        c.combat["parry"] = int(self.sp_parry.value())
        c.combat["dodge"] = int(self.sp_dodge.value())
        c.combat["initiative"] = int(self.sp_initiative.value())
        c.combat["actions_per_round"] = int(self.sp_actions.value())

        vehicles: dict[str, list[str]] = {"landcraft": [], "watercraft": [], "aircraft": []}
        for key in ("landcraft", "watercraft", "aircraft"):
            section = self.vehicle_sections.get(key, {})
            combos: list[QComboBox] = section.get("combos", [])
            picked: list[str] = []
            for cb in combos:
                name = str(cb.currentData() or "")
                if name:
                    picked.append(name)
            vehicles[key] = picked
        try:
            setattr(c, "vehicles", vehicles)
        except Exception:
            pass

        c.bio_e["total"] = int(self.sp_bio_total.value())
        c.bio_e["spent"] = int(self.sp_bio_spent.value())

        # Original animal characteristics (display-only, but saved for convenience)
        c.bio_e["original"] = {
            "size_level": self.ed_bio_orig_size_level.text().strip(),
            "length": self.ed_bio_orig_length.text().strip(),
            "weight": self.ed_bio_orig_weight.text().strip(),
            "build": self.ed_bio_orig_build.text().strip(),
        }

        # Mutant size selection (spend)
        c.bio_e["mutant_size_level"] = int(self.cb_bio_mutant_size_level.currentData() or 0)

        # Human features
        c.bio_e["human_features"] = {
            "hands_cost": int(self.cb_human_hands.currentData() or 0),
            "biped_cost": int(self.cb_human_biped.currentData() or 0),
            "speech_cost": int(self.cb_human_speech.currentData() or 0),
            "looks_cost": int(self.cb_human_looks.currentData() or 0),
            "hands_label": self.cb_human_hands.currentText(),
            "biped_label": self.cb_human_biped.currentText(),
            "speech_label": self.cb_human_speech.currentText(),
            "looks_label": self.cb_human_looks.currentText(),
        }

        # Natural weapons
        nw: list[dict[str, Any]] = []
        for cb in getattr(self, "bio_weapon_combos", []):
            data = cb.currentData()
            if isinstance(data, dict):
                nw.append({"name": str(data.get("name", "")), "cost": int(data.get("cost", 0) or 0)})
        c.bio_e["natural_weapons"] = nw

        # Abilities
        ab: list[dict[str, Any]] = []
        for cb in getattr(self, "bio_ability_combos", []):
            data = cb.currentData()
            if isinstance(data, dict):
                ab.append({"name": str(data.get("name", "")), "cost": int(data.get("cost", 0) or 0)})
        c.bio_e["abilities"] = ab

        # Psionics
        ps: list[dict[str, Any]] = []
        for cb in getattr(self, "bio_psionic_combos", []):
            label = cb.currentText()
            cost = int(cb.currentData() or 0) if cb.isEnabled() else 0
            if "None" not in label and cost > 0:
                ps.append({"name": label.split(" (", 1)[0], "cost": cost})
        c.bio_e["psionics"] = ps

        # Notes/traits
        traits = [line.strip() for line in self.ed_traits.toPlainText().splitlines() if line.strip()]
        c.bio_e["traits"] = traits

        image_path = getattr(c, "image_path", None) or getattr(c, "bio_e", {}).get("image_path")

        if image_path:
            pix = QPixmap(image_path)
            if not pix.isNull():
                self.lbl_character_art.setPixmap(
                    pix.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                try:
                    self.current_character.image_path = image_path
                except Exception:
                    pass

        return c

    def load_into_editor(self, c: Character, path: Optional[Path]) -> None:
        self.current_character = c
        self.current_path = path

        self.ed_name.setText(c.name)

        animal_source = (
            getattr(c, "animal_source", None)
            or getattr(c, "bio_e", {}).get("animal_source", None)
        )

        animal_type = (
            getattr(c, "animal_type", None)
            or getattr(c, "bio_e", {}).get("animal_type", None)
        )

        animal = (
            getattr(c, "animal", "") 
            or getattr(c, "bio_e", {}).get("animal", "")
            or ""
        )

        if isinstance(animal_source, str) and animal_source:
            idx = self.cb_animal_source.findData(animal_source)
            self.cb_animal_source.setCurrentIndex(idx if idx != -1 else 0)
        else:
            self.cb_animal_source.setCurrentIndex(0)

        self.on_animal_source_changed()

        if isinstance(animal_type, str) and animal_type:
            idx = self.cb_animal_type.findData(animal_type)
            self.cb_animal_type.setCurrentIndex(idx if idx != -1 else 0)
        else:
            self.cb_animal_type.setCurrentIndex(0)

        self.on_animal_type_changed()

        if isinstance(animal, str) and animal:
            idx = self.cb_animal.findData(animal)
            self.cb_animal.setCurrentIndex(idx if idx != -1 else 0)
        else:
            self.cb_animal.setCurrentIndex(0)

        if isinstance(getattr(c, "alignment", ""), str) and c.alignment:
            idx = self.cb_alignment.findData(c.alignment)
            self.cb_alignment.setCurrentIndex(idx if idx != -1 else 0)
        else:
            self.cb_alignment.setCurrentIndex(0)

        self.ed_age.setText(getattr(c, "age", "") or "")
        self.ed_gender.setText(getattr(c, "gender", "") or "")

        self.ed_weight.setText(getattr(c, "weight", "") or "")
        self.ed_height.setText(getattr(c, "height", "") or "")

        self.sp_total_credits.setValue(int(getattr(c, "total_credits", 0) or 0))
        self.ed_total_wealth.setText(str(getattr(c, "total_wealth", 0) or 0))

        self.sp_xp.setValue(int(getattr(c, "xp", 0) or 0))
        self.sp_level.setValue(int(getattr(c, "level", 1) or 1))
        self.sp_hp.setValue(int(getattr(c, "hit_points", 0) or 0))
        self.sp_sdc.setValue(int(getattr(c, "sdc", 0) or 0))

        weapons_selected = getattr(c, "weapons_selected", []) or []
        for i, cb in enumerate(self.weapon_combos):
            desired = str(weapons_selected[i]) if i < len(weapons_selected) else ""
            idx = cb.findData(desired)
            cb.setCurrentIndex(idx if idx != -1 else 0)
            self.on_weapon_changed(i)

        armor_type = str(getattr(c, "armor_type", "") or "")
        idx = self.cb_armor.findData(armor_type)
        if idx == -1:
            idx = self.cb_armor.findText(armor_type)
        self.cb_armor.setCurrentIndex(idx if idx != -1 else 0)

        self.ed_armor_name.setText(getattr(c, "armor_name", "") or "")

        if idx != -1 and armor_type:
            self.on_armor_changed()
        else:
            self.sp_armor_ar.setValue(int(getattr(c, "armor_ar", 0) or 0))
            self.sp_armor_sdc.setValue(int(getattr(c, "armor_sdc", 0) or 0))
        self.sync_defense_summary_fields()


        shield_type = str(getattr(c, "shield_type", "") or "")
        idx = self.cb_shield.findData(shield_type)
        if idx == -1:
            idx = self.cb_shield.findText(shield_type)
        self.cb_shield.setCurrentIndex(idx if idx != -1 else 0)
        self.ed_shield_notes.setText(str(getattr(c, "shield_notes", "") or ""))
        self.on_shield_changed()

        gear_selected = getattr(c, "gear_selected", []) or []
        for i, cb in enumerate(self.gear_combos):
            desired = str(gear_selected[i]) if i < len(gear_selected) else ""
            idx = cb.findData(desired)
            cb.setCurrentIndex(idx if idx != -1 else 0)
            self.on_gear_changed(i)

        self.ed_armor_name.setText(getattr(c, "armor_name", "") or "")

        # If armor exists in catalog use catalog values
        if armor_type and armor_type in ARMOR_BY_NAME:
            self.on_armor_changed()
        else:
            self.sp_armor_ar.setValue(int(getattr(c, "armor_ar", 0) or 0))
            self.sp_armor_sdc.setValue(int(getattr(c, "armor_sdc", 0) or 0))

        self.ed_notes.setPlainText(getattr(c, "notes", "") or "")

        for key, sp in self.attribute_fields.items():
            sp.setValue(int(getattr(c, "attributes", {}).get(key, 0)))

        pro_list = getattr(c, "skills", {}).get("pro", [""] * 10)
        ama_list = getattr(c, "skills", {}).get("amateur", [""] * 15)
        pro_list = (pro_list + [""] * 10)[:10]
        ama_list = (ama_list + [""] * 15)[:15]

        for i, cb in enumerate(self.pro_skill_boxes):
            desired = pro_list[i] or ""
            idx = cb.findData(desired, role=Qt.UserRole)
            cb.setCurrentIndex(idx if idx != -1 else 0)

        for i, cb in enumerate(self.amateur_skill_boxes):
            desired = ama_list[i] or ""
            idx = cb.findData(desired, role=Qt.UserRole)
            cb.setCurrentIndex(idx if idx != -1 else 0)

        training_name = str(getattr(c, "combat", {}).get("training", "None") or "None")
        idx = self.cb_combat_training.findData(training_name)
        self.cb_combat_training.setCurrentIndex(idx if idx != -1 else 0)

        auto_details = bool(getattr(c, "combat", {}).get("auto_details", True))
        self.chk_combat_auto_details.setChecked(auto_details)

        override = bool(getattr(c, "combat", {}).get("override", False))
        self.chk_combat_override.setChecked(override)
        self._set_combat_spinboxes_editable(override)

        if override:
            self.sp_strike.setValue(int(getattr(c, "combat", {}).get("strike", 0)))
            self.sp_parry.setValue(int(getattr(c, "combat", {}).get("parry", 0)))
            self.sp_dodge.setValue(int(getattr(c, "combat", {}).get("dodge", 0)))
            self.sp_initiative.setValue(int(getattr(c, "combat", {}).get("initiative", 0)))
            self.sp_actions.setValue(int(getattr(c, "combat", {}).get("actions_per_round", 2)))

        if not auto_details:
            self.ed_combat_training_details.setPlainText(str(getattr(c, "combat", {}).get("training_details_text", "")))

        vehicles = getattr(c, "vehicles", {}) or {}
        for section_key in ("landcraft", "watercraft", "aircraft"):
            picked = vehicles.get(section_key, []) if isinstance(vehicles, dict) else []
            section = self.vehicle_sections.get(section_key, {})
            combos: list[QComboBox] = section.get("combos", [])
            for i, cb in enumerate(combos):
                desired = str(picked[i]) if i < len(picked) else ""
                idx = cb.findData(desired)
                cb.setCurrentIndex(idx if idx != -1 else 0)
                self.on_vehicle_changed(section_key, i)

        self.sp_bio_total.setValue(int(getattr(c, "bio_e", {}).get("total", 0)))
        self.sp_bio_spent.setValue(int(getattr(c, "bio_e", {}).get("spent", 0)))

        original = getattr(c, "bio_e", {}).get("original", {}) or {}
        if isinstance(original, dict):
            self.ed_bio_orig_size_level.setText(str(original.get("size_level", "") or ""))
            self.ed_bio_orig_length.setText(str(original.get("length", "") or ""))
            self.ed_bio_orig_weight.setText(str(original.get("weight", "") or ""))
            self.ed_bio_orig_build.setText(str(original.get("build", "") or ""))

        mutant_size = int(getattr(c, "bio_e", {}).get("mutant_size_level", 0) or 0)
        if mutant_size:
            idx = self.cb_bio_mutant_size_level.findData(mutant_size)
            self.cb_bio_mutant_size_level.setCurrentIndex(idx if idx != -1 else 0)

        hf = getattr(c, "bio_e", {}).get("human_features", {}) or {}
        if isinstance(hf, dict):
            for cb, key in (
                (self.cb_human_hands, "hands_cost"),
                (self.cb_human_biped, "biped_cost"),
                (self.cb_human_speech, "speech_cost"),
                (self.cb_human_looks, "looks_cost"),
            ):
                cost = int(hf.get(key, 0) or 0)
                idx = cb.findData(cost)
                cb.setCurrentIndex(idx if idx != -1 else 0)

        image_path = getattr(c, "image_path", None) or getattr(c, "bio_e", {}).get("image_path")

        if image_path:
            pix = QPixmap(image_path)
            if not pix.isNull():
                self.lbl_character_art.setPixmap(
                    pix.scaled(240, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
            else:
                self.lbl_character_art.clear()
                self.lbl_character_art.setText("No Image")
        else:
            self.lbl_character_art.clear()
            self.lbl_character_art.setText("No Image")


        # Re-populate per-animal lists first (based on current animal)
        # so that combos have correct options before selecting saved items.
        self.on_bioe_animal_selected()

        saved_nw = getattr(c, "bio_e", {}).get("natural_weapons", []) or []
        if isinstance(saved_nw, list):
            for i, cb in enumerate(getattr(self, "bio_weapon_combos", [])):
                desired = saved_nw[i].get("name") if i < len(saved_nw) and isinstance(saved_nw[i], dict) else ""
                if desired:
                    # find by text
                    idx = cb.findText(desired, Qt.MatchFixedString)
                    cb.setCurrentIndex(idx if idx != -1 else 0)
                else:
                    cb.setCurrentIndex(0)

        saved_ab = getattr(c, "bio_e", {}).get("abilities", []) or []
        if isinstance(saved_ab, list):
            for i, cb in enumerate(getattr(self, "bio_ability_combos", [])):
                desired = saved_ab[i].get("name") if i < len(saved_ab) and isinstance(saved_ab[i], dict) else ""
                if desired:
                    idx = cb.findText(desired, Qt.MatchFixedString)
                    cb.setCurrentIndex(idx if idx != -1 else 0)
                else:
                    cb.setCurrentIndex(0)

        saved_ps = getattr(c, "bio_e", {}).get("psionics", []) or []
        if isinstance(saved_ps, list):
            # psionic combos store cost as data; match by power name prefix
            for i, cb in enumerate(getattr(self, "bio_psionic_combos", [])):
                desired = saved_ps[i].get("name") if i < len(saved_ps) and isinstance(saved_ps[i], dict) else ""
                if desired and cb.isEnabled():
                    # match by startswith
                    found = 0
                    for j in range(cb.count()):
                        if cb.itemText(j).startswith(desired):
                            found = j
                            break
                    cb.setCurrentIndex(found)
                else:
                    cb.setCurrentIndex(0)

        traits = getattr(c, "bio_e", {}).get("traits", []) or []
        self.ed_traits.setPlainText("\n".join(str(t) for t in traits))

        self.update_psionic_availability()
        self.recalc_bioe_spent()
        traits = getattr(c, "bio_e", {}).get("traits", []) or []
        self.ed_traits.setPlainText("\n".join(str(t) for t in traits))

        self.recalc_skill_displays()
        self.recalc_combat_from_training()
        self.recalc_total_wealth()
        self.recalc_weight_breakdown()


        if path:
            self.statusBar().showMessage(f"Loaded: {path.name}")
        else:
            self.statusBar().showMessage("New (unsaved) character")

        self.on_skills_changed()