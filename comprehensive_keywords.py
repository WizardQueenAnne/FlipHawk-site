"""
Comprehensive keywords database for FlipHawk marketplace scrapers.
Includes variations, misspellings, and specific model identifiers to improve matching.
"""

def get_keywords_for_subcategory(subcategory, fallback_to_direct=True):
    """
    Get a list of keywords for a specific subcategory.
    
    Args:
        subcategory (str): The subcategory to get keywords for
        fallback_to_direct (bool): If True, return the subcategory as a keyword when not found
        
    Returns:
        list: A list of keywords for the subcategory, or [subcategory] if not found and fallback enabled
    """
    for category, subcats in COMPREHENSIVE_KEYWORDS.items():
        if subcategory in subcats:
            return subcats[subcategory]
    
    # If not found and fallback is enabled, return the subcategory itself as a keyword
    if fallback_to_direct:
        return [subcategory.lower()]
    return []

COMPREHENSIVE_KEYWORDS = {
    "Tech": {
        "Headphones": [
            # Apple AirPods variations
            "airpods", "airpod", "air pods", "air pod", "apple earbuds", "apple earpods",
            "airpods pro", "airpods max", "airpods 2", "airpods 3", "airpods pro 2",
            "airpds", "aripos", "aripods", "apods", "ap pods", "apple airpads",
            "airpods 2nd gen", "airpods 3rd gen", "airpods generation", "airpod pros",
            "apple airpods pro 2", "airpods pro second generation", "airpods usb-c",
            
            # Beats variations
            "beats", "beats headphones", "beats solo", "beats studio", "beats pro",
            "beats studio buds", "beats fit pro", "powerbeats", "powerbeats pro",
            "beets", "bats headphones", "beatz", "bts headphones", "beat headphones",
            "beats solo 3", "beats solo3", "beats studio 3", "beats studio3",
            "beats by dre", "beats by dr dre", "beats wireless", "beat earbuds",
            
            # Bose variations
            "bose", "bose headphones", "bose quietcomfort", "bose 700", "bose qc",
            "bose nc", "bose earbuds", "bose soundsport", "bose qc35", "bose qc45",
            "boss headphones", "boze", "bosee", "quiet comfort", "bose 35 ii",
            "bose qc35 ii", "bose qc 45", "bose 700 nc", "bose noise cancelling",
            "bose quietcomfort 35", "bose quietcomfort 45", "bose sport earbuds",
            
            # Sony variations
            "sony wh", "sony headphones", "sony wf", "sony xm4", "sony xm5",
            "sony wh-1000xm4", "sony wh-1000xm5", "sony wf-1000xm4", "sony wf-1000xm5",
            "sonny headphones", "soney", "sony x1000", "sony wh1000", "sony wf1000",
            "sony 1000xm4", "sony 1000xm5", "sony xb900n", "sony wh-xb900n",
            "sony whch710n", "sony wh-ch710n", "sony linkbuds", "sony earbuds",
            
            # General terms and other brands
            "wireless headphones", "bluetooth earbuds", "noise cancelling",
            "anc headphones", "true wireless", "earphones", "ear buds",
            "sennheiser", "jabra", "jbl", "marshall", "skullcandy",
            "samsung buds", "galaxy buds", "pixel buds", "raycon", "anker soundcore",
            "bluetooth headset", "wireless earphones", "tws earbuds", "over ear headphones",
            "on ear headphones", "in ear headphones", "earbuds wireless", "earphone bluetooth",
            
            # Additional high-end brands
            "bang olufsen", "b&o", "bowers wilkins", "master dynamic", "audeze", "grado",
            "focal", "beyerdynamic", "audio technica", "ath", "shure", "akg", "klipsch",
            "bang and olufsen", "bowers & wilkins", "master & dynamic", "b and o"
        ],
        
        "Keyboards": [
            # Mechanical keyboards
            "mechanical keyboard", "mech keyboard", "gaming keyboard", "rgb keyboard",
            "cherry mx", "custom keyboard", "hot swap keyboard", "60% keyboard",
            "65% keyboard", "75% keyboard", "tkl keyboard", "full size keyboard",
            "mechancial", "mechanicl", "mech kybd", "mechanica keyboard",
            "tenkeyless", "tenkeyless keyboard", "keeb", "mechanical keeb",
            
            # Switch types
            "cherry mx red", "cherry mx blue", "cherry mx brown", "cherry mx black",
            "cherry mx silent", "gateron switch", "kailh switch", "topre switch",
            "box jade", "box navy", "holy panda", "zealio", "tealio", "bobagum",
            "tactile switch", "linear switch", "clicky switch", "optical switch",
            
            # Popular brands
            "logitech keyboard", "corsair keyboard", "razer keyboard", "keychron",
            "ducky keyboard", "das keyboard", "hyperx keyboard", "steelseries keyboard",
            "logitec", "corsare", "razor", "steel series", "keycrn", "keychrone",
            "glorious keyboard", "gmmk", "gmmk pro", "drop keyboard", "wasd keyboard",
            "varmilo", "leopold", "cooler master", "coolermaster", "filco", "akko",
            
            # Specific models
            "logitech g915", "corsair k70", "razer huntsman", "ducky one 2",
            "keychron k2", "anne pro", "gmmk pro", "keyboard and mouse combo",
            "corair k95", "razr black widow", "ducky on2", "anna pro",
            "logitech mx keys", "logitech g pro", "corsair k65", "razer blackwidow",
            "hyperx alloy", "steelseries apex", "ducky one 3", "keychron q1", "keychron v1",
            
            # Wireless options
            "wireless keyboard", "bluetooth keyboard", "wireless mechanical",
            "2.4ghz keyboard", "usb-c keyboard", "multi-device keyboard",
            "blutooth keyboard", "wi-fi keyboard", "usbc", "wireless gaming keyboard",
            "low profile keyboard", "low-profile", "ultra thin keyboard", "thin keyboard",
            
            # Accessories
            "keycaps", "pbt keycaps", "abs keycaps", "keyboard foam", "keyboard lube",
            "custom keycaps", "artisan keycap", "keyboard stabs", "keyboard stabilizers",
            "keyboard case", "keyboard plate", "keyboard pcb", "keyboard cable",
            "coiled cable", "aviator cable", "keyboard wrist rest"
        ],
        
        "Graphics Cards": [
            # NVIDIA cards
            "rtx 3050", "rtx 3060", "rtx 3060 ti", "rtx 3070", "rtx 3070 ti", 
            "rtx 3080", "rtx 3080 ti", "rtx 3090", "rtx 3090 ti",
            "rtx 4060", "rtx 4060 ti", "rtx 4070", "rtx 4070 ti", 
            "rtx 4080", "rtx 4090", "rtx 4090 ti",
            "geforce rtx", "nvidia gpu", "gtx 1660", "gtx 1660 super", "gtx 1660 ti",
            "gtx 1650", "gtx 1650 super", "gtx 1050", "gtx 1050 ti", "gtx 1080", "gtx 1080 ti", "gtx 1070", "gtx 1070 ti",
            "rtx 3080ti", "rtx 3070ti", "rtx3090", "rtx4090", "nividia",
            "rtx thirty eighty", "rtx thirty ninety", "rtx forty ninety",
            "nvidia card", "geforce card", "geforce gtx", "rtx card", "gtx card",
            "gddr6", "gddr6x", "ray tracing gpu", "dlss gpu", "ai gpu",
            
            # AMD cards
            "amd rx", "radeon rx", "rx 6500", "rx 6600", "rx 6600 xt", "rx 6650 xt",
            "rx 6700", "rx 6700 xt", "rx 6750 xt", "rx 6800", "rx 6800 xt", "rx 6900 xt", "rx 6950 xt",
            "rx 7600", "rx 7700 xt", "rx 7800 xt", "rx 7900 xt", "rx 7900 xtx",
            "radeon gpu", "amd radeon", "rx 580", "rx 570", "rx 5700", "rx 5700 xt", "rx 5600 xt",
            "vega 56", "vega 64", "amd vega", "radeon vega", "radeon 5000", "radeon 6000", "radeon 7000",
            "radion", "amd gpu", "rdna 2", "rdna 3", "rx6800xt", "rx6900xt",
            "amd card", "radeon card", "radion card", "fsr gpu",
            
            # Intel cards
            "intel arc", "intel arc a770", "intel arc a750", "intel arc a580", "intel arc a380",
            "intel gpu", "intel graphics card", "intl arc", "intel arc alchemist",
            
            # Brands
            "asus gpu", "msi gpu", "evga gpu", "gigabyte gpu", "zotac gpu",
            "asus rog gpu", "msi gaming x", "evga ftw3", "gigabyte aorus", "zotac amp",
            "pny gpu", "sapphire gpu", "xfx gpu", "powercolor gpu", "asrock gpu",
            "founders edition", "fe gpu", "nvidia fe", "reference card", "aib card",
            
            # General terms
            "graphics card", "video card", "gpu", "gaming gpu", "mining gpu",
            "workstation gpu", "professional gpu", "quadro", "firepro", "nvidia quadro",
            "amd firepro", "nvidia rtx a", "nvidia a series", "compute gpu", "ai accelerator",
            "grphics card", "grfx card", "videoscard", "vga card",
            "dual gpu", "triple fan gpu", "water cooled gpu", "liquid cooled gpu", "hybrid gpu",
            "overclocked gpu", "factory oc", "low profile gpu", "half height gpu", "single slot gpu"
        ],
        
        "CPUs": [
            # Intel processors
            "intel i3", "intel i5", "intel i7", "intel i9", "core i3", "core i5", "core i7", "core i9",
            "intel core", "intel cpu", "intel processor", "intel chip", "intel desktop cpu",
            "i3-12100", "i3-13100", "i5-12400", "i5-12600k", "i5-13400", "i5-13600k",
            "i7-12700k", "i7-13700k", "i9-12900k", "i9-13900k", "i9-14900k", "lga 1700", "lga 1200",
            "intel 12th gen", "intel 13th gen", "intel 14th gen", "intel alder lake", "intel raptor lake",
            "intel meteor lake", "intel arrow lake", "intel xeon", "intel celeron", "intel pentium",
            "intel eye7", "intl i7", "intell", "core eye 7", "core i series",
            
            # AMD processors
            "amd ryzen", "ryzen 3", "ryzen 5", "ryzen 7", "ryzen 9", "threadripper",
            "amd cpu", "amd processor", "amd chip", "amd desktop cpu",
            "ryzen 5600", "ryzen 5600x", "ryzen 5700x", "ryzen 5800x", "ryzen 5800x3d",
            "ryzen 7600", "ryzen 7600x", "ryzen 7700", "ryzen 7700x", "ryzen 7800x3d",
            "ryzen 7900x", "ryzen 7950x", "ryzen threadripper", "ryzen threadripper pro",
            "am4 cpu", "am5 cpu", "ryzen 5000", "ryzen 7000", "ryzen 8000",
            "amd zen 3", "amd zen 4", "amd zen 5",
            "ryzan", "rizen", "amd ryzn", "ryen", "thred ripper", "thread ripper",
            
            # ARM processors
            "arm cpu", "arm processor", "apple m1", "apple m2", "apple m3",
            "m1 chip", "m2 chip", "m3 chip", "m1 pro", "m1 max", "m1 ultra",
            "m2 pro", "m2 max", "m2 ultra", "m3 pro", "m3 max", "m3 ultra",
            "qualcomm snapdragon", "snapdragon processor", "microsoft sq", "microsoft sq chip",
            
            # General terms
            "processor", "cpu", "desktop cpu", "laptop cpu", "gaming cpu",
            "workstation cpu", "server cpu", "processer", "proccessor",
            "multi core cpu", "multi-core", "8 core", "10 core", "12 core", "16 core", "24 core", "32 core",
            "overclocking cpu", "unlocked cpu", "high performance cpu", "budget cpu", "entry level cpu",
            "cpu cooler", "air cooler", "liquid cooler", "aio cooler", "heatsink",
            "cpu socket", "cpu motherboard", "cpu ram compatibility"
        ],
        
        "Laptops": [
            # MacBooks - expanded
            "macbook", "macbook pro", "macbook air", "mac book", "macbookpro",
            "m1 macbook", "m2 macbook", "m3 macbook", "apple laptop",
            "mac pro", "mac air", "mackbook", "macbok", "mac book pro",
            "macbook pro 13", "macbook pro 14", "macbook pro 16", "macbook air 13",
            "macbook pro m1", "macbook pro m2", "macbook pro m3", "macbook air m1",
            "macbook air m2", "macbook 2020", "macbook 2021", "macbook 2022", "macbook 2023",
            "macbook pro 2020", "macbook pro 2021", "macbook pro 2022", "macbook pro 2023",
            "macbook pro retina", "macbook pro touchbar", "macbook pro 13 inch",
            "macbook pro 14 inch", "macbook pro 16 inch", "macbook air 13 inch",
            "magsafe", "apple silicon", "apple m chip", "apple m series",
            
            # Gaming laptops - expanded
            "gaming laptop", "rog laptop", "legion laptop", "msi laptop",
            "alienware laptop", "razer blade", "asus rog", "predator laptop",
            "gamming laptop", "rogen laptop", "alisware", "razr blade",
            "asus rog strix", "rog zephyrus", "rog flow", "rog ally", "msi ge76",
            "msi gs66", "msi stealth", "msi katana", "msi raider", "legion 5", "legion 5 pro",
            "legion 7", "legion slim", "alienware m15", "alienware m16", "alienware x14", "alienware x16", "alienware x17",
            "razer blade 14", "razer blade 15", "razer blade 16", "razer blade 17", "razer blade 18", "acer predator helios",
            "acer nitro", "hp omen", "rtx laptop", "rtx 3060 laptop", "rtx 3070 laptop", "rtx 3080 laptop",
            "rtx 4050 laptop", "rtx 4060 laptop", "rtx 4070 laptop", "rtx 4080 laptop", "rtx 4090 laptop",
            "gaming notebook", "gaming pc laptop", "gamer laptop", "high performance laptop",
            "high refresh laptop", "144hz laptop", "240hz laptop", "360hz laptop",
            
            # Business laptops - expanded
            "thinkpad", "dell xps", "hp elitebook", "surface laptop",
            "business laptop", "ultrabook", "2-in-1 laptop", "chromebook",
            "think pad", "dell xbs", "hp elite", "surface book",
            "thinkpad x1", "thinkpad carbon", "thinkpad extreme", "thinkpad t14", "thinkpad p1", 
            "dell xps 13", "dell xps 15", "dell xps 17", "dell latitude", "dell precision",
            "hp spectre", "hp envy", "hp pavilion", "hp probook", "hp zbook",
            "surface laptop 4", "surface laptop 5", "surface book 3", "surface pro",
            "lenovo yoga", "lenovo ideapad", "lenovo flex", "microsoft surface",
            "asus zenbook", "asus vivobook", "acer swift", "acer aspire", "acer chromebook",
            "samsung galaxy book", "samsung notebook", "lg gram", "huawei matebook",
            
            # General terms - expanded
            "laptop computer", "notebook", "gaming notebook", "laptop pc",
            "labtop", "lap top", "note book", "leptop", "portable computer",
            "intel laptop", "amd laptop", "ryzen laptop", "i7 laptop",
            "i9 laptop", "16gb ram laptop", "32gb ram laptop", "touch screen laptop",
            "touchscreen laptop", "4k laptop", "oled laptop", "student laptop",
            "budget laptop", "thin and light", "lightweight laptop", "ultraportable",
            "long battery", "all day battery", "video editing laptop", "photo editing laptop",
            "content creation laptop", "streaming laptop", "developer laptop", "programming laptop",
            "workstation laptop", "cad laptop", "3d modeling laptop", "ai laptop",
            "convertible laptop", "detachable laptop", "tablet laptop", "2-in-1", "2 in 1",
            "backlit keyboard", "numpad", "numeric keypad", "fingerprint reader", "webcam",
            "hdmi port", "usb-c", "thunderbolt", "sd card reader", "ethernet port"
        ],
        
        "Monitors": [
            # Gaming monitors
            "gaming monitor", "144hz monitor", "165hz monitor", "240hz monitor", "360hz monitor", "390hz monitor",
            "4k monitor", "2k monitor", "1440p monitor", "ultrawide monitor", "curved monitor",
            "super ultrawide", "qhd monitor", "qd-oled monitor", "ips monitor", "va monitor", "tn monitor", "oled monitor",
            "gamign monitor", "144 hz", "240 hz", "fourk monitor", "1440p", "2560x1440", "3440x1440", "3840x2160",
            "high refresh monitor", "fast response monitor", "1ms monitor", "low input lag", "g-sync monitor", "freesync monitor",
            "adaptive sync", "hdr monitor", "hdr400", "hdr600", "hdr1000", "displayhdr", "gaming display",
            
            # Brands and models
            "lg ultragear", "lg monitor", "samsung odyssey", "samsung monitor", "asus rog monitor", "asus monitor",
            "acer predator", "acer monitor", "dell monitor", "alienware monitor", "hp monitor", "benq monitor", "viewsonic monitor",
            "msi monitor", "gigabyte monitor", "aoc monitor", "eve spectrum", "corsair monitor", "philips monitor",
            "lg ultra gear", "samsuung", "rog swift", "predater monitor", "acer nitro", "dell ultrasharp",
            
            # Professional monitors
            "4k professional", "color accurate monitor", "design monitor", "photo editing monitor",
            "video editing monitor", "content creation monitor", "srgb monitor", "adobe rgb monitor",
            "dci-p3 monitor", "rec709 monitor", "color calibrated", "professional display", "reference monitor",
            "color acurate", "profesional monitor", "adobe rgb", "studio monitor", "production monitor",
            "color grading monitor", "graphic design monitor", "cad monitor", "medical imaging monitor",
            
            # General specifications
            "ips panel", "va panel", "tn panel", "oled panel", "mini-led", "qled", "nano ips",
            "100% srgb", "100% adobe rgb", "100% dci-p3", "10-bit monitor", "10bit color", "8-bit+frc",
            "vesa mount", "vesa compatible", "monitor arm", "monitor stand", "monitor riser",
            "usb-c monitor", "thunderbolt monitor", "daisy chain", "kvm switch", "monitor hub",
            "eye care monitor", "low blue light", "flicker free", "anti-glare", "matte display",
            "glossy display", "borderless monitor", "frameless monitor", "slim bezel",
            
            # Sizes and types
            "24 inch monitor", "27 inch monitor", "32 inch monitor", "34 inch monitor", "38 inch monitor",
            "49 inch monitor", "24in monitor", "27in monitor", "32in monitor", "dual monitor", "triple monitor",
            "portable monitor", "touchscreen monitor", "touch screen monitor", "drawing monitor", "pen display",
            "smart monitor", "tv monitor", "gaming tv", "external monitor", "second screen"
        ],
        
        "SSDs": [
            # Popular brands
            "samsung ssd", "samsung evo", "samsung pro", "samsung 970", "samsung 980", "samsung 990",
            "crucial ssd", "crucial mx500", "crucial p3", "crucial p5", "crucial p5 plus",
            "western digital ssd", "wd ssd", "wd black", "wd blue", "sandisk ssd", "sandisk extreme",
            "kingston ssd", "kingston fury", "kingston nv1", "kingston kc3000", "sk hynix ssd",
            "corsair ssd", "corsair mp600", "sabrent ssd", "sabrent rocket", "teamgroup ssd", "addlink ssd",
            "samsuung ssd", "cruicial", "westurn digital", "sanddisc", "kingson", "kioxia",
            
            # Storage capacities
            "128gb ssd", "256gb ssd", "512gb ssd", "500gb ssd", "1tb ssd", "2tb ssd", "4tb ssd", "8tb ssd",
            "128 gb ssd", "256 gb ssd", "512 gb ssd", "500 gb ssd", "1 tb ssd", "2 tb ssd", "4 tb ssd", "8 tb ssd",
            "1 terabyte ssd", "2 terabyte ssd", "half terabyte ssd", "quarter terabyte ssd",
            
            # Types and interfaces
            "pcie ssd", "pcie 3.0 ssd", "pcie 4.0 ssd", "pcie 5.0 ssd", "gen3 ssd", "gen4 ssd", "gen5 ssd",
            "nvme ssd", "nvme m.2", "m.2 ssd", "m.2 2280", "m.2 2242", "m.2 22110", "sata ssd", "sata iii",
            "msata", "u.2 ssd", "add-in card ssd", "aic ssd", "m key", "b key", "b+m key",
            "tlc ssd", "mlc ssd", "qlc ssd", "slc ssd", "3d nand", "v-nand",
            
            # External and portable
            "portable ssd", "external ssd", "usb ssd", "usb-c ssd", "thunderbolt ssd", "gaming ssd",
            "rugged ssd", "waterproof ssd", "shockproof ssd", "durable ssd", "backup ssd",
            "solid state", "solid state drive", "solidsate drive", "solid-state drive",
            
            # Performance metrics
            "high speed ssd", "fast ssd", "high performance ssd", "high endurance ssd",
            "ssd cache", "ssd boot drive", "ssd game drive", "ssd upgrade",
            "read speed", "write speed", "transfer speed", "iops", "tbw", "terabytes written",
            "heatsink ssd", "heatspreader", "ps5 compatible", "ps5 ssd", "xbox series x ssd"
        ],
        
        "Routers": [
            # Popular brands
            "netgear router", "netgear nighthawk", "netgear orbi", "tp link router", "tp-link archer",
            "asus router", "asus rog router", "asus zen wifi", "linksys router", "linksys velop",
            "google nest wifi", "google wifi", "amazon eero", "eero router", "ubiquiti router",
            "ubiquiti unifi", "ubiquiti amplifi", "netgeer", "tp-link", "tplink", "linksis", "googl wifi",
            "d-link router", "belkin router", "arris router", "motorola router", "synology router",
            
            # Technologies
            "wifi 6 router", "wifi 6e router", "wifi 7 router", "ax router", "be router", "ac router",
            "802.11ax router", "802.11be router", "802.11ac router", "mesh wifi", "mesh network", "mesh system",
            "gaming router", "5g router", "lte router", "4g router", "tri band router", "dual band router",
            "wi-fi 6", "wi-fi 6e", "wi-fi 7", "wfi router", "wifi raouter", "roter", "ruter",
            "gigabit router", "multi-gigabit", "2.5g router", "10g router", "10 gigabit",
            "vpn router", "secure router", "parental control router", "smart router",
            
            # Models
            "archer ax73", "archer ax90", "archer ax6000", "nighthawk rax80", "nighthawk rax120",
            "asus rt-ax88u", "asus rt-ax86u", "asus gt-ax11000", "linksys mr9600", "orbi rbk852",
            "eero pro 6", "eero pro 6e", "google wifi pack", "nest wifi pro", "deco x60", "deco xe75",
            "rog rapture", "rog strix", "netgear raxe500", "ubiquiti dream router", "synology rt6600ax",
            
            # Features and specifications
            "router modem combo", "modem router", "gateway router", "all in one router", "router access point",
            "long range router", "high power router", "coverage router", "whole home wifi",
            "smart home router", "iot router", "alexa compatible router", "homekit router",
            "mu-mimo router", "ofdma router", "beamforming", "high gain antennas", "external antennas",
            "qos router", "traffic prioritization", "bandwidth management", "guest network",
            "port forwarding", "dmz router", "firewall router", "secure dns", "wpa3 router",
            
            # Accessories and add-ons
            "wifi extender", "range extender", "wifi booster", "wifi repeater", "access point",
            "ethernet cable", "cat 6 cable", "cat 7 cable", "cat 8 cable", "router power adapter",
            "router mount", "wall mount", "ceiling mount", "router cooling", "router fan"
        ],
        
        "Vintage Tech": [
            # Classic audio devices
            "walkman", "sony walkman", "cassette walkman", "cd walkman", "minidisc walkman",
            "discman", "sony discman", "portable cd player", "minidisc player", "dat player",
            "ipod classic", "ipod nano", "ipod shuffle", "ipod mini", "ipod touch", "ipod video",
            "mp3 player", "creative zen", "zune", "sandisk sansa", "iriver", "archos",
            "walk man", "disc man", "i pod", "classic ipod", "ipod 160gb", "ipod 80gb", "ipod 30gb",
            "vintage audio", "portable cassette", "portable stereo", "boombox", "ghetto blaster",
            
            # Retro gaming handhelds
            "gameboy", "game boy", "gameboy color", "gameboy advance", "gameboy pocket", "gameboy micro",
            "game boy color", "game boy advance", "game boy pocket", "game boy micro", "gba", "gbc",
            "nintendo ds", "nintendo ds lite", "nintendo dsi", "nintendo 3ds", "nintendo 2ds",
            "psp", "psp 1000", "psp 2000", "psp 3000", "psp go", "ps vita", "playstation portable",
            "playstation vita", "sega game gear", "atari lynx", "neo geo pocket", "wonderswan",
            "game boy advance sp", "nintendo gameboy", "nintendo handhelds", "retro handheld",
            
            # Vintage computers and consoles
            "commodore 64", "commodore 128", "commodore vic-20", "commodore amiga", "amiga 500",
            "amiga 1200", "atari 800", "atari st", "atari 2600", "atari 5200", "atari 7800", "atari jaguar",
            "nes", "nintendo nes", "famicom", "super nintendo", "snes", "super famicom", "nintendo 64", "n64",
            "sega genesis", "sega mega drive", "sega master system", "sega saturn", "sega dreamcast",
            "neo geo", "neo geo aes", "turbografx", "pc engine", "3do", "philips cdi", "vectrex",
            "comodore", "amega", "nintendo 64", "super nintendo", "nintendos", "segga", "vintage console",
            "retro console", "vintage computer", "retro computer", "vintage game system",
            
            # Vintage phones and PDAs
            "nokia 3310", "nokia 3390", "nokia 8110", "nokia n-gage", "nokia n95", "nokia 6310",
            "motorola razr", "motorola startac", "motorola dynatac", "motorola microtac", "flip phone",
            "blackberry", "blackberry bold", "blackberry curve", "blackberry pearl", "blackberry passport",
            "palm pilot", "palm treo", "palm pre", "handspring visor", "compaq ipaq", "hp ipaq",
            "nokia brick", "razor phone", "black berry", "vintage cell", "vintage mobile", "pda",
            "sidekick phone", "t-mobile sidekick", "old smartphone", "early smartphone", "brick phone",
            
            # Vintage cameras and photo equipment
            "polaroid camera", "polaroid 600", "polaroid sx-70", "polaroid spectra", "polaroid land camera",
            "kodak camera", "kodak instamatic", "kodak disc", "kodak brownie", "kodak retina",
            "film camera", "35mm camera", "slr camera", "rangefinder camera", "twin lens reflex",
            "medium format camera", "large format camera", "instant camera", "analog camera", "vintage camera",
            "lomography", "lomo camera", "holga", "diana camera", "disposable camera", "film photography",
            "darkroom equipment", "photo enlarger", "developing tank", "vintage tripod", "vintage flash"
        ]
    },
    
    "Collectibles": {
        "Pokémon": [
            # Card types
            "pokemon cards", "pokemon card lot", "pokemon booster box", "pokemon tcg",
            "pokemon etb", "pokemon elite trainer box", "pokemon graded cards",
            "charizard card", "pikachu card", "japanese pokemon cards", "pokemon psa",
            "pokemom cards", "pokmon", "pokeman", "pocket monsters", "pokemon collection",
            "pokemon sealed", "pokemon wotc", "pokemon shadowless", "pokemon 1st edition",
            
            # Specific sets
            "base set", "shadowless", "1st edition", "neo genesis", "team rocket",
            "hidden fates", "shining fates", "evolving skies", "brilliant stars", "silver tempest",
            "crown zenith", "scarlet violet", "fusion strike", "chilling reign", "vivid voltage",
            "first edition", "1st ed", "baseset", "x y cards", "sun moon", "black white",
            "cosmic eclipse", "sword shield", "burning shadows", "ancient origins", "xy evolutions",
            
            # PSA grades
            "psa 10", "psa 9", "psa 8", "psa 7", "beckett graded", "cgc graded", "bgs graded",
            "gem mint", "mint condition", "near mint", "bgs 9.5", "cgc 9", "sgc graded",
            "graded pokemon", "slabbed pokemon", "graded card", "mint pokemon", "nm pokemon",
            
            # Popular characters
            "charizard vmax", "rainbow charizard", "pikachu vmax", "pikachu v", "mewtwo v",
            "blastoise", "venusaur", "umbreon", "lugia", "rayquaza", "mew", "eevee", "gengar",
            "charzard", "pickachu", "mewto", "blastios", "vingosaur", "reyquaza", "pikchu",
            "alt art pokemon", "full art pokemon", "pokemon ex", "pokemon gx", "pokemon v",
            "pokemon vmax", "pokemon vstar", "hyper rare pokemon", "ultra rare pokemon",
            
            # Card types and terminology
            "holo pokemon", "reverse holo", "secret rare", "ultra rare", "full art",
            "rainbow rare", "alternate art", "gold card", "trainer card", "energy card",
            "pokemon promos", "black star promo", "prerelease pokemon", "jumbo card",
            "error card", "miscut", "misprint", "proxy card", "fake pokemon"
        ],
        
        "Magic: The Gathering": [
            # Product types
            "mtg cards", "magic cards", "mtg booster box", "commander deck", "magic the gathering",
            "mtg bundle", "collector booster", "set booster", "draft booster", "mtg sealed",
            "magik cards", "mgic the gathering", "magic gathering", "tcg magic", "mtg lot",
            "mtg collection", "mtg deck", "mtg prerelease", "mtg fat pack", "mtg theme booster",
            
            # Sets and editions
            "alpha mtg", "beta mtg", "unlimited", "revised", "arabian nights",
            "antiquities", "legends", "modern horizons", "commander legends", "dominaria",
            "innistrad", "ravnica", "zendikar", "mirrodin", "kamigawa", "phyrexia",
            "alpa", "betta", "arbian nights", "modrn horizons", "4th edition", "5th edition",
            "new phyrexia", "innestrad", "strixhaven", "eldraine", "kaldheim",
            
            # Card types and terminology
            "mtg rare", "mtg mythic", "mtg uncommon", "mtg common", "foil mtg", "etched foil",
            "showcase frame", "borderless mtg", "extended art", "alternate art", "full art",
            "mtg proxy", "mtg alter", "mtg misprint", "mtg miscut", "mtg signed",
            "magic planeswalker", "magic creature", "magic instant", "magic sorcery", "magic artifact",
            
            # Popular cards
            "black lotus", "mox sapphire", "dual lands", "force of will", "mox pearl", "mox ruby",
            "wurmcoil engine", "tarmogoyf", "jace the mind sculptor", "volcanic island", "underground sea",
            "blak lotus", "mox saphire", "duel lands", "taramgoyf", "jayce", "lili of the veil",
            "goyf", "snapcaster", "cyclonic rift", "fetch lands", "shock lands", "reserve list",
            
            # Formats
            "mtg standard", "mtg modern", "mtg legacy", "mtg vintage", "mtg commander",
            "mtg edh", "mtg draft", "mtg sealed", "mtg brawl", "mtg pioneer",
            "mtg pauper", "mtg cube", "mtg limited", "mtg constructed"
        ],
        
        "Yu-Gi-Oh": [
            # Product types
            "yugioh cards", "yu-gi-oh cards", "yugioh deck", "structure deck",
            "yugioh booster box", "yugioh tin", "yugioh mega tin", "yugioh collection",
            "yugioih", "yu gi oh", "duelist cards", "ygo cards", "konami cards",
            "yugioh core set", "yugioh starter deck", "yugioh special edition", "yugioh speed duel",
            
            # Popular cards
            "blue eyes white dragon", "dark magician", "red eyes black dragon", "exodia",
            "pot of greed", "monster reborn", "egyptian god cards", "obelisk", "slifer", "ra",
            "blue eye", "dark magican", "red eys", "egodia", "blue eyes ultimate", "dark magician girl",
            "kaiba", "yugi", "joey", "ash blossom", "ghost belle", "effect veiler", "hand trap",
            
            # Sets and rarities
            "lob", "legend of blue eyes", "metal raiders", "magic ruler", "pharaoh's servant",
            "ghost rare", "starlight rare", "ultimate rare", "prismatic secret", "collector's rare",
            "ultra rare", "secret rare", "super rare", "common", "gold rare", "platinum rare",
            "legand of blue eye", "metal raider", "gost rare", "maximum gold", "battles of legend",
            
            # Card types and terminology
            "yugioh monster", "yugioh spell", "yugioh trap", "effect monster", "normal monster",
            "fusion monster", "synchro monster", "xyz monster", "link monster", "pendulum monster",
            "ritual monster", "tuner monster", "token card", "field spell", "counter trap",
            "first edition", "unlimited edition", "graded yugioh", "psa yugioh", "misprint yugioh"
        ],
        
        "Funko Pops": [
            # General
            "funko pop", "pop vinyl", "funko soda", "funko exclusive", "funko lot",
            "chase funko", "flocked funko", "metallic funko", "gitd funko", "glow in dark funko",
            "funco pop", "funko pops", "pop figure", "bobblehead", "vinyl figure",
            "funko collection", "funko display", "funko protector", "funko pop lot", "funko grail",
            
            # Popular lines
            "marvel funko", "dc funko", "star wars funko", "anime funko", "disney funko",
            "dbz funko", "naruto funko", "horror funko", "game of thrones funko", "stranger things funko",
            "mrvel funko", "starwars funko", "dragonball funko", "harry potter funko", "pokemon funko",
            "pop animation", "pop movies", "pop television", "pop games", "pop rocks", "pop ad icons",
            
            # Exclusives
            "comic con exclusive", "sdcc funko", "nycc funko", "eccc funko", "wondercon funko",
            "target exclusive", "walmart exclusive", "hot topic exclusive", "box lunch exclusive",
            "fye exclusive", "gamestop exclusive", "7-eleven exclusive", "amazon exclusive",
            "san diego comic con", "new york comic con", "emerald city", "funko shop exclusive",
            
            # Special types
            "funko pop ride", "funko pop town", "funko pop moment", "funko pop deluxe",
            "funko pop 2-pack", "funko pop 3-pack", "jumbo funko", "super sized funko",
            "pocket pop", "pop keychain", "pop pin", "art series", "cover art",
            "diamond collection", "chrome funko", "gold funko", "holiday funko", "convention exclusive"
        ],
        
        "Sports Cards": [
            # Types
            "basketball cards", "football cards", "baseball cards", "soccer cards", "hockey cards",
            "nba cards", "nfl cards", "mlb cards", "rookie cards", "sports card lot",
            "basket ball cards", "foot ball cards", "base ball cards", "sports card collection",
            "vintage sports cards", "graded sports cards", "sealed sports cards", "wax pack", "box break",
            
            # Brands
            "panini prizm", "topps chrome", "bowman chrome", "upper deck", "fleer ultra",
            "select", "mosaic", "optic", "donruss", "hoops", "chronicles", "leaf", "sage",
            "panini prism", "tops chrome", "upperdeck", "mosaik", "donruss elite", "contenders",
            "immaculate", "national treasures", "definitive", "gold standard", "spectra", "noir",
            
            # Popular players
            "michael jordan", "lebron james", "tom brady", "patrick mahomes", "aaron rodgers",
            "luka doncic", "shohei ohtani", "mike trout", "connor mcdavid", "wayne gretzky",
            "jordon cards", "labron james", "mahommes", "mcdavid cards", "giannis", "steph curry",
            "zion williamson", "ja morant", "trae young", "kobe bryant", "aaron judge", "vladimir guerrero",
            
            # Card types and terminology
            "autograph card", "auto card", "jersey card", "patch card", "relic card", "memorabilia card",
            "1/1 card", "one of one", "parallel card", "insert card", "refractor", "numbered card",
            "short print", "sp card", "ssp card", "ultra rare", "case hit", "hobby exclusive",
            "retail exclusive", "on card auto", "sticker auto", "rc card", "rpa card"
        ],
        
        "Comic Books": [
            # Publishers
            "marvel comics", "dc comics", "image comics", "dark horse comics", "boom studios",
            "idw comics", "vertigo comics", "valiant comics", "dynamite comics", "archie comics",
            "marval comics", "detective comics", "independant comics", "alternative comics", "manga",
            
            # Popular titles
            "amazing spider-man", "detective comics", "batman", "superman", "x-men", 
            "avengers", "fantastic four", "iron man", "captain america", "hulk", "thor",
            "wonder woman", "flash", "aquaman", "green lantern", "daredevil", "punisher",
            "walking dead", "invincible", "saga", "hellboy", "spawn", "sandman", "watchmen",
            
            # Eras and grades
            "golden age comics", "silver age comics", "bronze age comics", "copper age comics", 
            "modern age comics", "cgc graded", "cbcs graded", "pgx graded", "raw comics",
            "cgc 9.8", "cgc 9.6", "cgc 9.4", "cbcs 9.8", "graded comic", "slabbed comic",
            
            # Key issues and terminology
            "key issue", "first appearance", "origin issue", "death issue", "variant cover",
            "sketch cover", "virgin cover", "exclusive cover", "retailer incentive", "chase cover",
            "comic run", "comic lot", "comic collection", "back issues", "floppy comics",
            "trade paperback", "graphic novel", "omnibus", "hardcover comic", "absolute edition",
            "signature series", "remarked comic", "signed comic", "comic art", "original art"
        ],
        
        "Action Figures": [
            # Brands
            "mcfarlane figures", "neca figures", "hasbro figures", "mattel figures", "bandai figures",
            "hot toys", "sideshow", "mezco", "s.h. figuarts", "mafex", "figma", "good smile",
            "nendoroid", "funko action figure", "marvel legends", "star wars black series",
            "gi joe classified", "marvel select", "dc multiverse", "transformers", "masters of the universe",
            
            # Types and franchises
            "1/6 scale figure", "1/12 scale figure", "1/4 scale figure", "6 inch figure", "3.75 inch figure",
            "marvel figure", "dc figure", "star wars figure", "wwe figure", "nba figure", "nfl figure",
            "anime figure", "mcu figure", "tmnt figure", "power rangers figure", "godzilla figure",
            "predator figure", "alien figure", "robocop figure", "terminator figure", "horror figure",
            
            # Condition and terminology
            "mib figure", "nib figure", "mosc figure", "loose figure", "complete figure", "moc figure",
            "mint in box", "mint on card", "sealed figure", "action figure lot", "figure collection",
            "vintage figure", "retro figure", "modern figure", "articulated figure", "poseable figure",
            "exclusive figure", "convention exclusive", "store exclusive", "chase figure", "variant figure",
            "action figure accessories", "figure stand", "figure base", "figure display", "diorama"
        ],
        
        "LEGO Sets": [
            # Themes
            "lego star wars", "lego harry potter", "lego marvel", "lego dc", "lego city",
            "lego technic", "lego creator", "lego architecture", "lego ideas", "lego friends",
            "lego ninjago", "lego castle", "lego space", "lego pirates", "lego train",
            "lego modular", "lego speed champions", "lego jurassic world", "lego minecraft", "lego disney",
            
            # Set types
            "lego set", "lego kit", "lego collection", "lego bundle", "lego lot",
            "lego sealed", "lego new", "lego used", "lego complete", "lego incomplete",
            "lego mib", "lego nisb", "lego nib", "lego vintage", "lego retired",
            "lego exclusive", "lego limited edition", "lego ucs", "lego moc", "lego instructions",
            
            # Parts and specifics
            "lego minifigure", "lego minifig", "lego figure", "lego parts", "lego pieces",
            "lego brick", "lego plate", "lego tile", "lego baseplate", "lego building",
            "lego vehicle", "lego ship", "lego aircraft", "lego train", "lego space ship",
            "lego castle", "lego house", "lego building", "lego diorama", "lego scene",
            
            # Specific popular sets
            "lego millennium falcon", "lego death star", "lego hogwarts", "lego batmobile", "lego ecto-1",
            "lego rollercoaster", "lego saturn v", "lego titanic", "lego colosseum", "lego taj mahal",
            "millenium falcon", "millennium falcon", "death star", "imperial star destroyer", "at-at",
            "hogwarts castle", "diagon alley", "daily bugle", "batcave", "ghostbusters"
        ]
    },
    
    "Vintage Clothing": {
        "Jordans": [
            # Models
            "jordan 1", "jordan 1 high", "jordan 1 mid", "jordan 1 low", "jordan 1 retro", "aj1", "air jordan 1",
            "jordan 2", "jordan 3", "jordan 4", "jordan 5", "jordan 6", "jordan 7", "jordan 8",
            "jordan 9", "jordan 10", "jordan 11", "jordan 12", "jordan 13", "jordan 14",
            "jordon 1", "jordans 1", "airjordan", "air jordans", "retro jordans", "og jordans",
            
            # Colorways
            "chicago jordan", "chicago 1", "bred jordan", "bred 1", "bred 4", "bred 11",
            "royal jordan", "royal 1", "shadow jordan", "shadow 1", "black cement 3", "white cement 3",
            "black cat 4", "fire red 4", "metallic 5", "infrared 6", "bordeaux 7", "aqua 8",
            "space jam 11", "flu game 12", "he got game 13", "last shot 14", "concord 11",
            "chicago 1s", "bread 1s", "royle blue", "shadows jordan", "cement 3s", "black toe",
            
            # Sizes and conditions
            "size 7 jordan", "size 8 jordan", "size 8.5 jordan", "size 9 jordan", "size 9.5 jordan",
            "size 10 jordan", "size 10.5 jordan", "size 11 jordan", "size 11.5 jordan", "size 12 jordan",
            "size 13 jordan", "size 14 jordan", "gs jordan", "youth jordan", "women jordan",
            "deadstock jordan", "ds jordan", "vnds jordan", "jordan lot", "used jordan", "worn jordan",
            "sz 10", "sz 11", "ded stock", "dead stock", "og all", "replacement box"
        ],
        
        "Nike Dunks": [
            # Models
            "nike dunk low", "nike dunk high", "dunk sb", "nike sb dunk", "nike dunk mid",
            "dunk low pro", "dunk high pro", "dunk low retro", "dunk high retro", "dunk premium",
            "nike dunks low", "nike dnk", "sb dunks", "dunks sb", "nike skate", "nike skateboarding",
            
            # Popular colorways
            "panda dunk", "next nature", "vintage green", "championship red", "coast dunk",
            "chicago dunk", "syracuse dunk", "unc dunk", "michigan dunk", "spartan green",
            "travis scott dunk", "strangelove dunk", "off white dunk", "grateful dead dunk",
            "safari dunk", "chunky dunky", "ray gun dunk", "plum dunk", "purple lobster",
            "panda dunks", "chicgo dunk", "syrucuse", "trav scott", "university blue", "brazil dunk",
            
            # Sizes and conditions
            "size 7 dunk", "size 8 dunk", "size 8.5 dunk", "size 9 dunk", "size 9.5 dunk",
            "size 10 dunk", "size 10.5 dunk", "size 11 dunk", "size 11.5 dunk", "size 12 dunk",
            "size 13 dunk", "size 14 dunk", "gs dunk", "youth dunk", "women dunk",
            "deadstock dunk", "ds dunk", "vnds dunk", "dunk lot", "used dunk", "worn dunk",
            "special box dunk", "dunk with special box", "dunk og all", "dunk no box"
        ],
        
        "Vintage Tees": [
            # Types
            "vintage band tee", "vintage rap tee", "vintage movie tee", "vintage anime tee",
            "vintage sports tee", "vintage concert tee", "bootleg tee", "vintage graphic tee",
            "vintge band t shirt", "vintage t shirt", "t-shirt vintage", "rock tee", "metal band tee",
            "hip hop tee", "promo tee", "tour tee", "movie promo shirt", "single stitch",
            
            # Brands
            "vintage nike", "vintage adidas", "vintage champion", "vintage tommy hilfiger",
            "vintage ralph lauren", "vintage harley davidson", "vintage nascar", "vintage stussy",
            "vintage supreme", "vintage carhartt", "vintage guess", "vintage levis", "vintage starter",
            "vintge nike", "vintage addidas", "champions vintage", "tommmy", "polo vintage",
            "vintage band", "vintage sports", "vintage rock", "vintage rap", "vintage logo",
            
            # Decades and styles
            "90s vintage", "80s vintage", "70s vintage", "y2k vintage", "00s vintage",
            "90s tee", "80s tee", "70s tee", "nineties vintage", "eighties", "y2k tee",
            "grunge tee", "skate tee", "surf tee", "rave tee", "club tee", "festival tee",
            "distressed vintage", "faded vintage", "worn in", "vintage look", "retro tee",
            
            # Popular bands and themes
            "nirvana tee", "metallica tee", "tupac tee", "biggie tee", "rolling stones tee",
            "grateful dead tee", "led zeppelin tee", "acdc tee", "guns n roses tee", "pink floyd tee",
            "beastie boys tee", "wu tang tee", "nwa tee", "run dmc tee", "public enemy tee",
            "iron maiden tee", "slayer tee", "megadeth tee", "snoop dogg tee", "dr dre tee"
        ],
        
        "Band Tees": [
            # Rock bands
            "nirvana shirt", "metallica shirt", "guns n roses shirt", "rolling stones shirt", "led zeppelin shirt",
            "pink floyd shirt", "acdc shirt", "aerosmith shirt", "queen shirt", "the who shirt",
            "black sabbath shirt", "deep purple shirt", "iron maiden shirt", "judas priest shirt", "motorhead shirt",
            "kiss shirt", "ramones shirt", "clash shirt", "sex pistols shirt", "dead kennedys shirt",
            
            # Metal bands
            "slayer shirt", "megadeth shirt", "anthrax shirt", "pantera shirt", "slipknot shirt",
            "tool shirt", "system of a down shirt", "korn shirt", "disturbed shirt", "rammstein shirt",
            "cannibal corpse shirt", "death shirt", "morbid angel shirt", "obituary shirt", "deicide shirt",
            "black metal shirt", "death metal shirt", "thrash metal shirt", "doom metal shirt", "nu metal shirt",
            
            # Hip hop and rap
            "tupac shirt", "biggie shirt", "wu tang shirt", "nwa shirt", "run dmc shirt",
            "public enemy shirt", "beastie boys shirt", "eminem shirt", "dr dre shirt", "snoop dogg shirt",
            "ice cube shirt", "eazy e shirt", "50 cent shirt", "jay z shirt", "nas shirt",
            "wu-tang clan", "notorious big", "2pac shirt", "a tribe called quest", "de la soul",
            
            # Pop and alternative
            "beatles shirt", "michael jackson shirt", "madonna shirt", "prince shirt", "david bowie shirt",
            "elton john shirt", "bob marley shirt", "fleetwood mac shirt", "radiohead shirt", "coldplay shirt",
            "green day shirt", "blink 182 shirt", "red hot chili peppers shirt", "foo fighters shirt", "pearl jam shirt",
            "soundgarden shirt", "alice in chains shirt", "stone temple pilots shirt", "rage against the machine shirt",
            
            # Types and styles
            "band tee", "concert shirt", "tour shirt", "vintage band tee", "bootleg band tee",
            "rock tee", "metal tee", "rap tee", "hip hop shirt", "official merchandise",
            "band merch", "retro band shirt", "graphic band tee", "music shirt", "artist shirt",
            "concert merch", "promo tee", "rare band shirt", "limited edition band shirt"
        ],
        
        "Denim Jackets": [
            # Brands
            "levis denim jacket", "wrangler denim jacket", "lee denim jacket", "gap denim jacket",
            "calvin klein denim jacket", "tommy hilfiger denim jacket", "guess denim jacket", "diesel denim jacket",
            "carhartt denim jacket", "dickies denim jacket", "ralph lauren denim jacket", "true religion denim jacket",
            "vintage levis", "levis trucker", "levis type 3", "levis type 2", "levis type 1",
            "japanese denim", "raw denim", "selvedge denim", "selvage denim", "sanforized denim",
            
            # Types and styles
            "jean jacket", "denim coat", "trucker jacket", "sherpa denim", "lined denim jacket",
            "oversized denim jacket", "cropped denim jacket", "distressed denim jacket", "acid wash denim jacket",
            "stone wash denim jacket", "bleached denim jacket", "faded denim jacket", "embroidered denim jacket",
            "patched denim jacket", "custom denim jacket", "painted denim jacket", "studded denim jacket",
            "black denim jacket", "blue denim jacket", "dark wash denim", "light wash denim", "medium wash denim",
            
            # Vintage and eras
            "vintage denim jacket", "80s denim jacket", "90s denim jacket", "70s denim jacket", "y2k denim jacket",
            "retro denim jacket", "vintage jean jacket", "vintage trucker jacket", "made in usa denim",
            "big e levis", "single stitch denim", "red tab levis", "orange tab levis", "501 levis",
            "type iii jacket", "type ii jacket", "type i jacket", "blanket lined denim", "heritage denim",
            
            # Themes and decorations
            "biker denim jacket", "punk denim jacket", "rock denim jacket", "grunge denim jacket", "skate denim jacket",
            "western denim jacket", "workwear denim jacket", "motorcycle denim jacket", "denim chore coat",
            "patched denim", "battle jacket", "kutte jacket", "band patches", "pin jacket", "chain jacket",
            "embellished denim", "beaded denim", "rhinestone denim", "graffiti denim", "airbrushed denim"
        ],
        
        "Designer Brands": [
            # Luxury fashion houses
            "gucci", "louis vuitton", "chanel", "prada", "dior", "versace", "fendi",
            "balenciaga", "saint laurent", "ysl", "valentino", "burberry", "hermes", "celine",
            "givenchy", "bottega veneta", "loewe", "balmain", "alexander mcqueen", "miu miu",
            "guccy", "luis vuitton", "loui vitton", "chanell", "prado", "dioor", "versachi",
            "fende", "balenciga", "yves saint laurent", "valintino", "burbury", "hermes paris",
            
            # Contemporary designer brands
            "off white", "fear of god", "vetements", "palm angels", "amiri", "rick owens",
            "comme des garcons", "acne studios", "maison margiela", "raf simons", "thom browne",
            "stone island", "bape", "supreme", "kith", "palace", "chrome hearts", "vlone",
            "off-white", "fog essentials", "vetemens", "cdg", "margeila", "mastermind japan",
            
            # Popular designer items
            "designer bag", "designer wallet", "designer belt", "designer shoes", "designer glasses",
            "designer sunglasses", "designer dress", "designer coat", "designer jacket", "designer denim",
            "designer tee", "designer hoodie", "designer sweater", "designer polo", "designer shirt",
            "designer watch", "designer jewelry", "designer scarf", "designer hat", "designer sneakers",
            
            # Authentication and condition
            "authentic designer", "guaranteed authentic", "authentic gucci", "authentic louis vuitton",
            "real designer", "fake designer", "replica designer", "counterfeit designer", "designer authentication",
            "new with tags", "nwt designer", "new with box", "used designer", "vintage designer",
            "rare designer", "limited edition designer", "runway piece", "sample piece", "archive designer",
            
            # Designer specifics
            "louis vuitton monogram", "lv damier", "lv epi", "lv canvas", "gucci gg", "gucci monogram",
            "chanel caviar", "chanel lambskin", "chanel flap", "hermes birkin", "hermes kelly", "hermes constance",
            "prada saffiano", "prada nylon", "fendi zucca", "fendi peekaboo", "burberry check", "burberry nova check",
            "dior saddle", "dior book tote", "ysl sunset", "ysl loulou", "balenciaga city", "balenciaga triple s"
        ],
        
        "Carhartt": [
            # Jacket and coat styles
            "carhartt detroit jacket", "carhartt chore coat", "carhartt active jacket", "carhartt duck jacket",
            "carhartt wip jacket", "carhartt quilted jacket", "carhartt lined jacket", "carhartt vest",
            "carhartt montana jacket", "carhartt bartlett jacket", "carhartt michigan coat", "carhartt og detroit",
            "detroit jacket", "chore coat", "duck jacket", "carhartt j130", "carhartt j131", "carhartt j140",
            
            # Pants and overalls
            "carhartt double knee", "carhartt carpenter pants", "carhartt work pants", "carhartt dungarees",
            "carhartt jeans", "carhartt overalls", "carhartt bib overalls", "carhartt cargo pants",
            "carhartt duck pants", "carhartt canvas pants", "carhartt b01", "carhartt b03", "carhartt b136",
            "double knee pants", "double front", "duck canvas pants", "firm duck", "loose fit", "relaxed fit",
            
            # Shirts
            "carhartt shirt", "carhartt tee", "carhartt long sleeve", "carhartt henley", "carhartt pocket tee",
            "carhartt work shirt", "carhartt button up", "carhartt flannel", "carhartt chamois", "carhartt thermal",
            "carhartt heavyweight", "carhartt logo shirt", "carhartt graphic tee", "carhartt pocket logo",
            "work shirt", "pocket tee", "heavyweight tee", "k87 tee", "k124 shirt", "relaxed fit shirt",
            
            # Hoodies and sweats
            "carhartt hoodie", "carhartt sweatshirt", "carhartt pullover", "carhartt crewneck", "carhartt zip up",
            "carhartt thermal sweatshirt", "carhartt rain defender", "carhartt midweight", "carhartt heavyweight",
            "carhartt logo hoodie", "carhartt script logo", "carhartt wip hoodie", "carhartt essentials",
            "hooded sweatshirt", "zip hoodie", "quarter zip", "full zip", "k121 hoodie", "k288 sweatshirt",
            
            # Accessories and other items
            "carhartt beanie", "carhartt hat", "carhartt watch hat", "carhartt cap", "carhartt bucket hat",
            "carhartt backpack", "carhartt bag", "carhartt belt", "carhartt wallet", "carhartt gloves",
            "carhartt socks", "carhartt bandana", "carhartt scarf", "carhartt boots", "carhartt shoes",
            "watch hat", "acrylic hat", "a18 beanie", "canvas bag", "legacy bag", "work gloves",
            
            # Colors and materials
            "carhartt brown", "carhartt duck brown", "carhartt black", "carhartt navy", "carhartt hamilton brown",
            "carhartt tan", "carhartt olive", "carhartt camo", "carhartt realtree", "carhartt mossy oak",
            "carhartt duck canvas", "carhartt cotton", "carhartt denim", "carhartt corduroy", "carhartt flannel",
            "carhartt sherpa", "carhartt quilted", "carhartt blanket lined", "carhartt fleece", "carhartt thermal",
            
            # Vintage and special editions
            "vintage carhartt", "made in usa carhartt", "carhartt wip", "carhartt work in progress",
            "carhartt heritage", "carhartt limited edition", "carhartt collaboration", "carhartt x",
            "carhartt streetwear", "carhartt archive", "carhartt 90s", "carhartt 80s", "carhartt deadstock",
            "union made carhartt", "big c logo", "j97 detroit", "santa fe jacket", "weathered duck", "broken in"
        ],
        
        "Patagonia": [
            # Jacket and fleece styles
            "patagonia fleece", "patagonia synchilla", "patagonia retro x", "patagonia retro pile",
            "patagonia snap t", "patagonia better sweater", "patagonia down jacket", "patagonia nano puff",
            "patagonia torrentshell", "patagonia rain jacket", "patagonia baggies jacket", "patagonia vest",
            "synchilla fleece", "retro pile", "snap-t pullover", "r1 fleece", "r2 fleece", "down sweater",
            "nano air", "micro puff", "torrentshell rain", "houdini jacket", "triolet jacket", "das parka",
            
            # Pants and shorts
            "patagonia baggies", "patagonia baggies shorts", "patagonia stand up shorts", "patagonia quandary pants",
            "patagonia venga rock pants", "patagonia gi pants", "patagonia hiking pants", "patagonia board shorts",
            "patagonia sweatpants", "patagonia all-wear shorts", "patagonia performance pants", "patagonia snow pants",
            "baggies 5\"", "baggies 7\"", "stand up shorts", "duck pants", "hemp pants", "capilene pants",
            "guidewater pants", "happy hike pants", "dirt craft pants", "powder bowl pants", "untracked pants",
            
            # Shirts and tops
            "patagonia tee", "patagonia t-shirt", "patagonia graphic tee", "patagonia long sleeve",
            "patagonia flannel", "patagonia button up", "patagonia polo", "patagonia organic cotton",
            "patagonia capilene", "patagonia base layer", "patagonia sun shirt", "patagonia responsibili-tee",
            "patagonia p-6 logo", "patagonia fitz roy", "patagonia flying fish", "fjord flannel", "pima cotton",
            "capilene cool", "capilene thermal", "capilene midweight", "tropic comfort", "sun stretch shirt",
            
            # Bags and accessories
            "patagonia backpack", "patagonia black hole", "patagonia duffel", "patagonia tote",
            "patagonia daypack", "patagonia sling", "patagonia messenger bag", "patagonia hip pack",
            "patagonia hat", "patagonia beanie", "patagonia cap", "patagonia gloves", "patagonia neck gaiter",
            "black hole backpack", "black hole duffel", "atom sling", "refugio pack", "altvia pack",
            "ultralight black hole", "stealth sling", "arbor pack", "duckbill cap", "fitz roy trout hat",
            
            # Vintage and special editions
            "vintage patagonia", "made in usa patagonia", "patagonia retro", "patagonia vintage",
            "patagonia rare", "patagonia deadstock", "patagonia limited edition", "patagonia collaboration",
            "patagonia early 90s", "patagonia late 80s", "patagonia classic", "patagonia yvon chouinard",
            "deep pile fleece", "pile fleece", "summit pack", "mars jacket", "guide jacket", "legacy collection",
            "worn wear", "silent down", "pataloha", "mars jacket", "legacy collection", "patented snap-t"
        ]
    },
    
    "Antiques": {
        "Coins": [
            # US coins
            "morgan dollar", "peace dollar", "buffalo nickel", "mercury dime", "barber dime",
            "kennedy half dollar", "walking liberty", "indian head penny", "wheat penny", "steel penny",
            "large cent", "flying eagle cent", "two cent piece", "three cent piece", "half dime",
            "seated liberty", "shield nickel", "v nickel", "barber quarter", "standing liberty quarter",
            "washington quarter", "silver quarter", "silver dime", "eisenhower dollar", "susan b anthony",
            
            # World coins
            "british sovereign", "canadian maple leaf", "mexican peso", "chinese panda", "french franc",
            "german mark", "italian lira", "spanish peseta", "russian ruble", "japanese yen",
            "australian dollar", "south african krugerrand", "austrian schilling", "dutch guilder", "swiss franc",
            "roman coin", "greek coin", "byzantine coin", "hammered coin", "milled coin",
            
            # Coin types and terminology
            "gold coin", "silver coin", "copper coin", "bronze coin", "platinum coin",
            "proof coin", "uncirculated coin", "mint state coin", "brilliant uncirculated", "bu coin",
            "ms70 coin", "ngc graded", "pcgs graded", "anacs graded", "slabbed coin",
            "error coin", "key date", "semi key", "double die", "off center", "clipped planchet",
            "mint error", "type coin", "year set", "mint set", "proof set", "commemorative coin",
            
            # Coin collections
            "coin collection", "coin lot", "coin album", "coin folder", "coin roll",
            "coin hoard", "coin stash", "coin estate", "coin inheritance", "numismatic collection",
            "ancient coins", "medieval coins", "colonial coins", "foreign coins", "world coins",
            "copper coins", "silver coins", "gold coins", "bullion coins", "investment coins"
        ],
        
        "Watches": [
            # Luxury brands
            "rolex watch", "omega watch", "patek philippe", "audemars piguet", "vacheron constantin",
            "jaeger lecoultre", "iwc watch", "panerai watch", "cartier watch", "breitling watch",
            "tudor watch", "tag heuer watch", "longines watch", "zenith watch", "grand seiko",
            "blancpain watch", "ulysse nardin", "chopard watch", "hublot watch", "bulgari watch",
            
            # Vintage and mid-range brands
            "vintage watch", "seiko watch", "citizen watch", "tissot watch", "oris watch",
            "hamilton watch", "bulova watch", "timex watch", "casio watch", "waltham watch",
            "elgin watch", "gruen watch", "benrus watch", "zodiac watch", "movado watch",
            "universal geneve", "enicar watch", "glycine watch", "doxa watch", "wittnauer watch",
            
            # Watch types and terminology
            "mechanical watch", "automatic watch", "manual wind watch", "quartz watch", "solar watch",
            "chronograph watch", "diver watch", "pilot watch", "field watch", "dress watch",
            "military watch", "railroad watch", "pocket watch", "wrist watch", "smart watch",
            "vintage timepiece", "luxury timepiece", "luxury watch", "swiss made", "swiss movement",
            
            # Watch components and characteristics
            "watch movement", "watch dial", "watch hands", "watch strap", "watch bracelet",
            "leather strap", "nato strap", "jubilee bracelet", "oyster bracelet", "president bracelet",
            "sapphire crystal", "acrylic crystal", "mineral crystal", "screw down crown", "helium escape valve",
            "water resistant", "waterproof watch", "luminous dial", "patina dial", "tropical dial",
            
            # Watch collections and models
            "rolex submariner", "rolex datejust", "rolex daytona", "rolex gmt", "rolex explorer",
            "omega speedmaster", "omega seamaster", "omega constellation", "patek nautilus", "patek aquanaut",
            "audemars royal oak", "cartier tank", "cartier santos", "iwc portuguese", "panerai luminor",
            "tudor black bay", "breitling navitimer", "tag heuer carrera", "seiko skx", "grand seiko snowflake"
        ],
        
        "Cameras": [
            # Camera brands
            "leica camera", "hasselblad camera", "rolleiflex camera", "nikon camera", "canon camera",
            "minolta camera", "olympus camera", "pentax camera", "mamiya camera", "contax camera",
            "bronica camera", "zeiss camera", "voigtlander camera", "polaroid camera", "kodak camera",
            "linhof camera", "sinar camera", "deardorff camera", "graflex camera", "horseman camera",
            
            # Camera types
            "rangefinder camera", "slr camera", "tlr camera", "view camera", "large format camera",
            "medium format camera", "35mm camera", "half frame camera", "instant camera", "folding camera",
            "box camera", "point and shoot", "compact camera", "panoramic camera", "stereo camera",
            "toy camera", "disposable camera", "pinhole camera", "spy camera", "underwater camera",
            
            # Film formats and types
            "film camera", "35mm film", "120 film", "220 film", "4x5 film", "8x10 film",
            "sheet film", "roll film", "polaroid film", "instax film", "pack film",
            "black and white film", "color film", "slide film", "negative film", "infrared film",
            "reversal film", "kodachrome", "ektachrome", "tri-x", "hp5", "portra", "velvia",
            
            # Camera lenses
            "camera lens", "prime lens", "zoom lens", "wide angle lens", "telephoto lens",
            "normal lens", "macro lens", "fisheye lens", "portrait lens", "leica lens",
            "zeiss lens", "voigtlander lens", "nikkor lens", "canon lens", "minolta lens",
            "mamiya lens", "hasselblad lens", "large format lens", "anamorphic lens", "cine lens",
            
            # Camera accessories and equipment
            "camera bag", "camera case", "camera strap", "lens cap", "lens hood",
            "tripod", "monopod", "light meter", "flash", "cable release",
            "film back", "focusing screen", "ground glass", "darkcloth", "loupe",
            "developing tank", "film scanner", "enlarger", "darkroom equipment", "camera repair kit"
        ],
        
        "Typewriters": [
            # Typewriter brands
            "remington typewriter", "underwood typewriter", "royal typewriter", "smith corona typewriter",
            "olivetti typewriter", "olympia typewriter", "hermes typewriter", "adler typewriter",
            "imperial typewriter", "continental typewriter", "facit typewriter", "erika typewriter",
            "corona typewriter", "hammond typewriter", "ibm typewriter", "selectric typewriter",
            "brother typewriter", "torpedo typewriter", "triumph typewriter", "wanderer typewriter",
            
            # Typewriter types and eras
            "antique typewriter", "vintage typewriter", "manual typewriter", "portable typewriter",
            "standard typewriter", "desktop typewriter", "electric typewriter", "electronic typewriter",
            "mechanical typewriter", "qwerty typewriter", "dvorak typewriter", "index typewriter",
            "victorian typewriter", "art deco typewriter", "mid century typewriter", "1920s typewriter",
            "1930s typewriter", "1940s typewriter", "1950s typewriter", "1960s typewriter",
            
            # Typewriter features and components
            "typewriter ribbon", "typewriter keys", "typewriter platen", "typewriter carriage",
            "type bars", "typewriter bell", "shift key", "space bar", "return lever", "margin stops",
            "ribbon selector", "tabulator", "paper bail", "line spacing", "backspace key",
            "ribbon spool", "typebar guide", "type segment", "type basket", "keyboard",
            
            # Typewriter condition and accessories
            "working typewriter", "functional typewriter", "typewriter repair", "typewriter restoration",
            "typewriter case", "typewriter cover", "typewriter manual", "typewriter desk", "typewriter table",
            "typewriter stand", "typewriter ribbon tin", "typewriter eraser", "typewriter brush",
            "typewriter oil", "typewriter cleaning kit", "typewriter service", "typewriter parts",
            "typewriter collector", "typewriter lot", "rare typewriter"
        ],
        
        "Vinyl Records": [
            # Record formats
            "vinyl record", "lp record", "45 rpm record", "78 rpm record", "33 rpm record",
            "7 inch record", "10 inch record", "12 inch record", "picture disc", "colored vinyl",
            "vinyl album", "ep record", "single record", "shellac record", "acetate record",
            "flexi disc", "box set", "vinyl collection", "record collection", "vinyl lot",
            
            # Musical genres
            "rock vinyl", "jazz vinyl", "blues vinyl", "soul vinyl", "r&b vinyl",
            "hip hop vinyl", "rap vinyl", "country vinyl", "folk vinyl", "classical vinyl",
            "pop vinyl", "punk vinyl", "metal vinyl", "progressive rock vinyl", "psychedelic vinyl",
            "soundtrack vinyl", "ambient vinyl", "electronic vinyl", "indie vinyl", "alternative vinyl",
            
            # Condition and grading
            "mint vinyl", "near mint vinyl", "vg+ vinyl", "vg vinyl", "g+ vinyl",
            "sealed vinyl", "unopened vinyl", "unplayed vinyl", "first pressing", "original pressing",
            "reissue vinyl", "repress vinyl", "180 gram vinyl", "200 gram vinyl", "half speed master",
            "direct to disc", "audiophile vinyl", "mono record", "stereo record", "quadraphonic record",
            
            # Record labels and terminology
            "rare vinyl", "collectible vinyl", "vintage vinyl", "antique records", "promo copy",
            "white label", "test pressing", "bootleg vinyl", "limited edition", "gatefold cover",
            "blue note records", "verve records", "columbia records", "rca records", "atlantic records",
            "decca records", "motown records", "chess records", "stax records", "sub pop records",
            
            # Record care and equipment
            "record player", "turntable", "vinyl cleaner", "record cleaner", "record brush",
            "record sleeve", "inner sleeve", "outer sleeve", "record jacket", "record album cover",
            "record storage", "record crate", "record cabinet", "record stand", "record display",
            "vinyl cleaning kit", "record weight", "record clamp", "record mat", "dust cover"
        ],
        
        "Vintage Tools": [
            # Hand tool types
            "vintage hand plane", "antique hand plane", "stanley plane", "block plane", "smoothing plane",
            "vintage saw", "handsaw", "backsaw", "crosscut saw", "rip saw", "dovetail saw",
            "vintage chisel", "antique chisel", "socket chisel", "tang chisel", "mortise chisel",
            "vintage hammer", "antique hammer", "claw hammer", "ball peen hammer", "sledge hammer",
            "vintage drill", "hand drill", "brace drill", "breast drill", "push drill", "bit and brace",
            
            # Tool brands
            "stanley tools", "disston tools", "millers falls", "sargent tools", "ohio tools",
            "union tools", "keen kutter", "blue grass tools", "witherby tools", "buck brothers",
            "lie nielsen", "bailey tools", "bedrock plane", "irwin tools", "craftsman tools",
            "fulton tools", "dunlap tools", "vaughan tools", "plumb tools", "estwing tools",
            
            # Woodworking tools
            "woodworking tools", "carpentry tools", "cabinetmaker tools", "joiner tools", "timber framing tools",
            "wood plane", "wood chisel", "drawknife", "spokeshave", "adze tool",
            "gouge tool", "carving tool", "marking gauge", "mortise gauge", "try square",
            "combination square", "bevel gauge", "miter box", "saw bench", "workbench",
            
            # Metalworking tools
            "blacksmith tools", "forge tools", "anvil", "vise", "machinist tools", 
            "bench vise", "leg vise", "post vise", "tool post", "metal lathe",
            "tin snips", "metal shears", "rivet tool", "tongs", "hammer and tongs",
            "metalworking hammer", "forge hammer", "sledge hammer", "ball-peen hammer", "cross-peen hammer",
            
            # Measurement and layout tools
            "vintage ruler", "folding ruler", "carpenter rule", "boxwood rule", "stanley rule",
            "vintage level", "spirit level", "plumb bob", "chalk line", "trammel points",
            "caliper tool", "divider tool", "compass tool", "marking knife", "scratch awl",
            "vintage tape measure", "measuring tools", "layout tools", "machinist square", "framing square"
        ],
        
        "Old Maps": [
            # Map types
            "antique map", "vintage map", "old map", "hand drawn map", "manuscript map",
            "world map", "continent map", "country map", "state map", "city map",
            "road map", "railway map", "nautical map", "sea chart", "celestial map",
            "star map", "topographical map", "geological map", "military map", "battle map",
            
            # Map eras
            "medieval map", "renaissance map", "18th century map", "19th century map", "early 20th century map",
            "victorian map", "edwardian map", "colonial map", "post-colonial map", "civil war map",
            "world war I map", "world war II map", "cold war map", "depression era map", "pre-war map",
            "mappa mundi", "ptolemaic map", "portolan chart", "explorers map", "discovery map",
            
            # Map makers and publishers
            "rand mcnally map", "national geographic map", "ordnance survey map", "sanborn map", "usgs map",
            "michelin map", "bartholomew map", "stanford map", "johnston map", "tallis map",
            "speed map", "ortelius map", "mercator map", "blaeu map", "visscher map",
            "mitchell map", "colton map", "h.c. tunison map", "cram map", "hammond map",
            
            # Map regions and subjects
            "european map", "american map", "asian map", "african map", "pacific map",
            "north america map", "south america map", "central america map", "caribbean map", "arctic map",
            "london map", "paris map", "new york map", "rome map", "tokyo map",
            "western hemisphere", "eastern hemisphere", "northern hemisphere", "southern hemisphere", "equatorial map",
            
            # Map formats and characteristics
            "folding map", "wall map", "pocket map", "atlas map", "globe map",
            "map book", "map collection", "map portfolio", "map set", "map series",
            "color map", "black and white map", "relief map", "political map", "physical map",
            "historical map", "commemorative map", "propaganda map", "pictorial map", "bird's-eye view"
        ]
    },
    
    "Gaming": {
        "Consoles": [
            # Nintendo consoles
            "nintendo switch", "nintendo switch lite", "nintendo switch oled", "nintendo wii", "nintendo wii u",
            "nintendo gamecube", "nintendo 64", "super nintendo", "super nes", "snes", "nes", "nintendo nes",
            "gameboy", "gameboy color", "gameboy advance", "gba", "nintendo ds", "nintendo 3ds", "nintendo 2ds",
            "nintende switch", "nintnedo 64", "n64", "supernintendo", "super famicom", "nes classic", "snes classic",
            
            # Sony consoles
            "playstation", "playstation 1", "ps1", "psone", "playstation 2", "ps2", "playstation 3", "ps3",
            "playstation 4", "ps4", "playstation 4 pro", "playstation 5", "ps5", "playstation 5 digital",
            "psp", "psp 1000", "psp 2000", "psp 3000", "psp go", "ps vita", "playstation vita", "ps tv",
            "playstaton", "play station", "ps4 slim", "ps4 pro", "ps5 disc", "ps5 digital", "playstaton portable",
            
            # Microsoft consoles
            "xbox", "xbox original", "xbox 360", "xbox 360 slim", "xbox 360 e", "xbox one", "xbox one s", 
            "xbox one x", "xbox series x", "xbox series s", "xbox elite", "xbox limited edition",
            "x box", "exbox", "xbox1", "xbone", "xbox 1", "xbox series", "xsx", "xss",
            
            # Retro consoles
            "atari 2600", "atari 5200", "atari 7800", "atari jaguar", "sega genesis", "sega mega drive",
            "sega master system", "sega saturn", "sega dreamcast", "neo geo", "neo geo aes", "neo geo mvs",
            "turbografx 16", "pc engine", "3do", "philips cdi", "vectrex", "intellivision", "colecovision",
            "atari", "atari system", "sega", "segga", "genesis", "megadrive", "dreamcst", "turbo grafx",
            
            # Modern retro consoles
            "retron", "retron 5", "retron 77", "analogue nt", "analogue super nt", "analogue mega sg",
            "polymega", "retrousb avs", "retro gaming console", "mini console", "classic console",
            "nes mini", "snes mini", "playstation classic", "sega genesis mini", "pc engine mini",
            "turbografx mini", "neo geo mini", "arcade1up", "evercade", "retro console", "handheld retro"
        ],
        
        "Game Controllers": [
            # Nintendo controllers
            "nintendo switch pro controller", "switch pro controller", "joy con", "joy-con", "joycon",
            "wii remote", "wiimote", "wii nunchuck", "wii classic controller", "wii u gamepad",
            "gamecube controller", "n64 controller", "super nintendo controller", "snes controller",
            "nes controller", "nintendo 64 controller", "joy con grip", "nintendo pro controller",
            
            # PlayStation controllers
            "playstation controller", "ps1 controller", "ps2 controller", "ps3 controller", "ps4 controller",
            "ps5 controller", "dualsense controller", "dualshock controller", "dualshock 4", "dualshock 3",
            "dualshock 2", "dualshock 1", "playstation move", "ps move", "ps5 dualsense", "ps4 dualshock",
            "duel shock", "dual shock", "ps controller", "playstation joystick", "playstation wheel",
            
            # Xbox controllers
            "xbox controller", "xbox one controller", "xbox series controller", "xbox 360 controller",
            "xbox duke controller", "xbox elite controller", "xbox paddle controller", "xbox adaptive controller",
            "xbox wireless controller", "xbox wired controller", "xbox s controller", "xbox original controller",
            "x box controller", "xbox remote", "xbone controller", "xbx controller", "xbox gamepad",
            
            # Third-party controllers
            "third party controller", "aftermarket controller", "hori controller", "madcatz controller",
            "pdp controller", "powera controller", "razer controller", "scuf controller", "thrustmaster controller",
            "logitech controller", "8bitdo controller", "retro-bit controller", "hyperkin controller",
            "arcade stick", "fight stick", "fighting controller", "racing wheel", "rock band controller",
            
            # Accessories and types
            "wireless controller", "wired controller", "bluetooth controller", "usb controller", "rf controller",
            "gamepad", "joystick", "arcade stick", "steering wheel", "guitar controller",
            "dance pad", "light gun", "vr controller", "motion controller", "flight stick",
            "controller adapter", "controller converter", "battery pack", "charging dock", "controller skin"
        ],
        
        "Rare Games": [
            # Nintendo rare games
            "earthbound snes", "chrono trigger", "little samson", "panic restaurant", "stadium events",
            "super mario rpg", "conker's bad fur day", "fire emblem path of radiance", "mega man x3", "mega man 7",
            "pokemon emerald", "pokemon crystal", "pokemon heartgold", "pokemon soulsilver", "pokemon box",
            "paper mario thousand year door", "metroid prime trilogy", "golden sun", "chibi robo", "path of radiance",
            
            # PlayStation rare games
            "suikoden ii", "valkyrie profile", "kuon", "rule of rose", "haunting ground",
            "silent hill shattered memories", "persona 2", "tales of destiny", "klonoa", "misadventures of tron bonne",
            "jojo's bizarre adventure", "blood will tell", "echo night", "dragon quest vii", "revelations persona",
            "xenogears", "einhander", "tomba", "wild arms", "mega man legends 2",
            
            # Xbox rare games
            "steel battalion", "jurassic park operation genesis", "stubbs the zombie", "panzer dragoon orta",
            "phantom dust", "otogi", "outrun 2006 coast 2 coast", "oddworld stranger's wrath", "metal wolf chaos",
            "jet set radio future", "blinx 2", "conker live and reloaded", "blood wake", "breakdown",
            "futurama", "grabbed by the ghoulies", "gun valkyrie", "ikaruga", "phantom crash",
            
            # Sega rare games
            "panzer dragoon saga", "panzer dragoon zwei", "shining force iii", "magic knight rayearth",
            "burning rangers", "astal", "albert odyssey", "dragon force", "guardian heroes",
            "lunar silver star story", "lunar eternal blue", "popful mail", "snatcher", "keio flying squadron",
            "crusader of centy", "ninja princess", "eliminate down", "lords of thunder", "pier solar",
            
            # General rare games
            "sealed video game", "factory sealed game", "complete in box", "cib game", "mint condition game",
            "new old stock game", "game lot", "game collection", "rare game", "valuable game",
            "obscure game", "limited release", "japan exclusive", "pal exclusive", "ntsc exclusive",
            "collector's edition", "limited edition", "promotional copy", "not for resale", "prototype game"
        ],
        
        "Arcade Machines": [
            # Arcade cabinet types
            "arcade cabinet", "arcade machine", "arcade game", "upright arcade", "cocktail arcade",
            "mini arcade", "bartop arcade", "pedestal arcade", "candy cabinet", "vewlix cabinet",
            "astro city cabinet", "new astro city", "blast city cabinet", "egret cabinet", "taito cabinet",
            "arcade1up", "countercade", "arcade marquee", "arcade control panel", "arcade monitor",
            
            # Popular arcade games
            "pac-man arcade", "ms pac-man arcade", "galaga arcade", "donkey kong arcade", "street fighter arcade",
            "mortal kombat arcade", "nba jam arcade", "space invaders arcade", "asteroids arcade", "centipede arcade",
            "defender arcade", "dig dug arcade", "frogger arcade", "galaxian arcade", "joust arcade",
            "mario bros arcade", "missile command arcade", "pole position arcade", "q*bert arcade", "robotron arcade",
            
            # Arcade components
            "arcade joystick", "arcade buttons", "arcade trackball", "arcade spinner", "arcade yoke",
            "arcade monitor", "arcade crt", "arcade pcb", "jamma board", "jamma harness",
            "arcade power supply", "arcade marquee", "arcade bezel", "arcade t-molding", "arcade coin door",
            "arcade coin mech", "arcade control panel", "arcade artwork", "arcade side art", "arcade kick plate",
            
            # Arcade manufacturers and terminology
            "atari arcade", "namco arcade", "midway arcade", "konami arcade", "taito arcade",
            "sega arcade", "capcom arcade", "nintendo arcade", "williams arcade", "gottlieb arcade",
            "neo geo mvs", "jamma arcade", "mame arcade", "multi game arcade", "multicade",
            "original arcade", "vintage arcade", "golden age arcade", "classic arcade", "retro arcade",
            
            # Arcade-related items
            "arcade restoration", "arcade repair", "arcade parts", "arcade manual", "arcade schematics",
            "arcade collector", "arcade auction", "arcade showroom", "arcade warehouse", "arcade room",
            "gameroom", "game room", "arcade artwork", "arcade decal", "arcade sticker",
            "arcade controller", "arcade stick", "arcade cabinet kit", "diy arcade", "mame cabinet"
        ],
        
        "Handhelds": [
            # Nintendo handhelds
            "gameboy", "game boy", "gameboy color", "gameboy advance", "gameboy advance sp", "gameboy micro",
            "nintendo ds", "nintendo ds lite", "nintendo dsi", "nintendo dsi xl", "nintendo 3ds",
            "nintendo 3ds xl", "new nintendo 3ds", "new nintendo 3ds xl", "nintendo 2ds", "nintendo 2ds xl",
            "gba", "gba sp", "gbc", "gbm", "game boy pocket", "game boy light", "ds", "dsl", "n3ds",
            
            # Sony handhelds
            "psp", "psp 1000", "psp 2000", "psp 3000", "psp go", "psp street", "playstation portable",
            "ps vita", "ps vita slim", "playstation vita", "ps tv", "playstation tv", "vita", "psvita",
            "psp fat", "psp slim", "psp brite", "ps vita oled", "ps vita lcd", "pch-1000", "pch-2000",
            
            # Sega handhelds
            "game gear", "sega game gear", "sega nomad", "sega genesis nomad", "sega genesis portable",
            "sega vmm", "vmm", "visual memory unit", "vmu", "sega master gear", "genesis portable",
            "sega portable", "sega handheld", "portable genesis", "sonic handheld", "game gear micro",
            
            # Other vintage handhelds
            "atari lynx", "neo geo pocket", "neo geo pocket color", "wonderswan", "wonderswan color",
            "game.com", "tiger electronics", "mattel electronics", "coleco handheld", "bandai lcd game",
            "game & watch", "game and watch", "pokemon mini", "pokemin", "pokemini", "digimon",
            "tamagotchi", "virtual pet", "giga pet", "nano pet", "digital pet", "electronic pet",
            
            # Modern handhelds
            "steam deck", "valve steam deck", "rog ally", "asus rog ally", "ayaneo", "ayaneo air",
            "ayaneo 2", "gpd win", "gpd win 2", "gpd win 3", "gpd win max", "onexplayer", "onexplayer mini",
            "retroid pocket", "anbernic", "rg351", "rg552", "miyoo mini", "powkiddy", "handheld pc",
            "gaming handheld", "portable pc", "windows handheld", "emulation handheld", "android handheld"
        ],
        
        "Gaming Headsets": [
            # Brands and models
            "astro gaming headset", "astro a40", "astro a50", "hyperx headset", "hyperx cloud", "hyperx cloud 2",
            "razer headset", "razer kraken", "razer blackshark", "logitech headset", "logitech g pro", "logitech g733",
            "steelseries headset", "steelseries arctis", "arctis 7", "arctis pro", "corsair headset", "corsair void",
            "corsair virtuoso", "sennheiser gaming", "sennheiser gsp", "audio technica gaming", "turtle beach headset",
            
            # Features and types
            "wireless gaming headset", "wired gaming headset", "wireless headphones", "wired headphones",
            "7.1 surround", "surround sound", "spatial audio", "noise cancelling", "gaming microphone",
            "detachable microphone", "retractable microphone", "boom mic", "rgb headset", "programmable headset",
            "lightweight headset", "comfort headset", "memory foam", "breathable ear cups", "cooling gel",
            
            # Platform compatibility
            "ps5 headset", "ps4 headset", "playstation headset", "xbox headset", "xbox series x headset",
            "xbox one headset", "nintendo switch headset", "pc gaming headset", "pc headset", "mac compatible",
            "multi platform headset", "cross platform headset", "universal gaming headset", "console headset",
            "mobile gaming headset", "bluetooth gaming headset", "usb headset", "3.5mm headset", "wireless dongle",
            
            # Gaming terms and terminology
            "pro gaming headset", "esports headset", "tournament headset", "competitive headset", "streamer headset",
            "gaming audio", "game sound", "footstep audio", "directional audio", "audio positioning",
            "mic monitoring", "sidetone", "game chat balance", "game mix", "voice chat",
            "gaming sound card", "dolby atmos", "dts headphone", "thx spatial", "virtual surround"
        ],
        
        "VR Gear": [
            # VR headsets
            "oculus quest", "oculus quest 2", "meta quest", "meta quest 2", "meta quest pro", "meta quest 3",
            "valve index", "htc vive", "htc vive pro", "htc vive cosmos", "htc vive focus", "playstation vr", "psvr",
            "playstation vr2", "psvr2", "hp reverb", "windows mixed reality", "samsung odyssey", "pimax",
            "oculus rift", "oculus rift s", "oculus go", "meta horizon", "vr headset", "virtual reality headset",
            
            # VR accessories
            "vr controllers", "vr motion controllers", "valve knuckles", "index controllers", "touch controllers",
            "vr base stations", "vr lighthouses", "vr sensors", "vr tracking", "vr headphones", "vr audio",
            "vr lens", "prescription lens", "vr lens adapter", "vr face cushion", "vr facial interface",
            "vr cover", "vr case", "vr stand", "vr mount", "headset display", "cable management", "vr pulley",
            
            # VR hardware and upgrades
            "vr ready pc", "oculus link", "oculus link cable", "virtual desktop", "wireless vr", "vr wireless adapter",
            "vr power bank", "vr battery pack", "extended battery", "vr graphics card", "vr gpu", "vr cpu",
            "vr cooling", "vr comfort", "vr resolution", "vr display", "vr screen", "vr refresh rate", "high fov",
            "wide field of view", "eye tracking", "face tracking", "full body tracking", "vr trackers",
            
            # VR gaming and apps
            "vr games", "vr gaming", "vr experience", "vr app", "vr software", "vr steam", "steamvr",
            "oculus store", "meta store", "sidequest", "beat saber", "half life alyx", "vr chat", "vrchat",
            "vr fitness", "vr workout", "vr social", "vr meeting", "vr movie", "vr video", "360 video",
            
            # VR terminology
            "virtual reality", "mixed reality", "augmented reality", "xr", "extended reality", "immersive",
            "6dof", "3dof", "room scale", "standing experience", "seated experience", "vr motion sickness",
            "vr comfort", "vr locomotion", "vr teleport", "vr smooth turning", "vr snap turning", "vr ipd"
        ]
    },
    
    "Music Gear": {
        "Electric Guitars": [
            # Brands
            "fender guitar", "gibson guitar", "prs guitar", "ibanez guitar", "esp guitar", "jackson guitar",
            "epiphone guitar", "squier guitar", "schecter guitar", "gretsch guitar", "charvel guitar", "evh guitar",
            "yamaha guitar", "guild guitar", "rickenbacker guitar", "musicman guitar", "ernie ball music man",
            "danelectro guitar", "reverend guitar", "g&l guitar", "suhr guitar", "strandberg guitar", "chapman guitar",
            
            # Models
            "stratocaster", "telecaster", "les paul", "sg guitar", "flying v", "explorer", "jazzmaster", "jaguar",
            "mustang guitar", "prs custom", "prs ce", "prs se", "ibanez rg", "ibanez s", "ibanez jem", "esp eclipse",
            "jackson soloist", "jackson dinky", "gretsch white falcon", "gretsch duo jet", "rickenbacker 330",
            "strat guitar", "tele guitar", "custom guitar", "les pol", "sg style", "v guitar", "hollow body",
            
            # Guitar specifics
            "electric guitar", "solid body guitar", "semi hollow guitar", "hollow body guitar", "vintage guitar",
            "custom shop guitar", "signature guitar", "guitar body", "guitar neck", "guitar fretboard", "guitar frets",
            "guitar tuners", "guitar bridge", "guitar pickups", "guitar electronics", "guitar wiring", "guitar nut",
            "guitar strings", "guitar strap", "guitar case", "guitar stand", "guitar wall hanger", "hardshell case",
            
            # Guitar electronics
            "humbucker pickup", "single coil pickup", "p90 pickup", "active pickup", "passive pickup", "emg pickup",
            "seymour duncan", "dimarzio pickup", "bare knuckle pickup", "pickup set", "guitar potentiometer",
            "guitar switch", "guitar jack", "guitar wiring", "guitar soldering", "guitar shielding", "guitar mod",
            "humbucker", "single coil", "p90", "gibson pickup", "fender pickup", "hot pickup", "vintage pickup",
            
            # Guitar condition and types
            "new guitar", "used guitar", "vintage guitar", "relic guitar", "aged guitar", "player grade",
            "mint condition", "guitar project", "partscaster", "project guitar", "guitar kit", "diy guitar",
            "left handed guitar", "lefty guitar", "right handed guitar", "short scale guitar", "baritone guitar",
            "extended range", "seven string", "8 string guitar", "7 string guitar", "multiscale guitar", "fanned fret"
        ],
        
        "Guitar Pedals": [
            # Pedal types
            "distortion pedal", "overdrive pedal", "fuzz pedal", "boost pedal", "delay pedal",
            "reverb pedal", "chorus pedal", "phase pedal", "flanger pedal", "tremolo pedal",
            "vibrato pedal", "wah pedal", "envelope filter", "eq pedal", "compressor pedal",
            "noise gate", "octave pedal", "pitch shifter", "harmonizer pedal", "looper pedal",
            
            # Pedal brands
            "boss pedal", "mxr pedal", "electro harmonix", "ehx pedal", "strymon pedal",
            "tc electronic", "walrus audio", "jhs pedal", "keeley pedal", "wampler pedal",
            "earthquaker devices", "death by audio", "chase bliss", "zvex pedal", "digitech pedal",
            "eventide pedal", "line 6 pedal", "source audio", "meris pedal", "neunaber pedal",
            
            # Specific pedal models
            "tube screamer", "ibanez ts9", "boss ds1", "rat distortion", "klon centaur",
            "big muff", "blues driver", "boss dd", "carbon copy", "strymon timeline",
            "strymon big sky", "ehx pog", "digitech whammy", "cry baby wah", "boss ce2",
            "small clone", "mxr phase 90", "univibe", "fuzz face", "boss rc",
            
            # Pedal components and features
            "guitar pedal", "effects pedal", "stompbox", "multi effect", "pedal board",
            "pedal power supply", "pedal patch cable", "pedal switcher", "true bypass", "buffered bypass",
            "analog pedal", "digital pedal", "vintage pedal", "boutique pedal", "clone pedal",
            "diy pedal", "pedal kit", "pedal mod", "pedal clone", "nos components",
            
            # Pedal-related terms and accessories
            "pedalboard", "pedal board", "pedaltrain", "temple audio", "pedal platform",
            "pedal case", "pedal bag", "pedal power", "isolated power", "voodoo lab",
            "cioks power", "1spot power", "patch cable", "pedal coupler", "pedal riser",
            "pedal velcro", "pedal tape", "pedal cable", "pedal chain", "signal path"
        ],
        
        "Synthesizers": [
            # Synthesizer types
            "analog synthesizer", "digital synthesizer", "modular synthesizer", "semi modular", "hybrid synthesizer",
            "monophonic synth", "polyphonic synth", "duophonic synth", "paraphonic synth", "virtual analog",
            "fm synthesizer", "wavetable synth", "additive synthesizer", "subtractive synthesizer", "granular synthesizer",
            "sample based synth", "rompler", "physical modeling", "vector synthesis", "linear arithmetic",
            
            # Synthesizer brands
            "moog synthesizer", "korg synthesizer", "roland synthesizer", "yamaha synthesizer", "sequential synth",
            "arturia synthesizer", "behringer synthesizer", "elektron synthesizer", "novation synthesizer", "dsi synth",
            "oberheim synthesizer", "arp synthesizer", "eurorack modular", "make noise", "doepfer",
            "nord synthesizer", "waldorf synthesizer", "modal electronics", "buchla synthesizer", "teenage engineering",
            
            # Popular models
            "minimoog", "moog model d", "moog grandmother", "moog matriarch", "moog one",
            "korg minilogue", "korg monologue", "korg prologue", "korg ms20", "korg arp odyssey",
            "roland jupiter", "roland juno", "roland system", "yamaha dx7", "yamaha reface",
            "prophet 5", "prophet 6", "prophet rev2", "ob-6", "oberheim ob-x8",
            "sequential pro 3", "op-1", "op-z", "mini nova", "ultranova",
            
            # Synthesizer components and features
            "vco", "voltage controlled oscillator", "dco", "digital oscillator", "vca", "voltage controlled amplifier",
            "vcf", "voltage controlled filter", "envelope generator", "adsr", "attack decay sustain release",
            "sequencer", "arpeggiator", "lfo", "low frequency oscillator", "eurorack module",
            "synthesizer keyboard", "synth keybed", "aftertouch", "mod wheel", "pitch bend",
            
            # Synthesizer connectivity and accessories
            "midi controller", "usb midi", "din midi", "cv gate", "control voltage",
            "audio interface", "synth case", "synth stand", "synthesizer dust cover", "synthesizer power supply",
            "patch cable", "patch bay", "patch book", "patch storage", "patch memory",
            "sustain pedal", "expression pedal", "synthesizer software", "daw integration", "hardware sequencer"
        ],
        
        "Vintage Amps": [
            # Tube amp brands
            "fender amp", "marshall amp", "vox amp", "orange amp", "ampeg amp",
            "mesa boogie", "hiwatt amp", "matchless amp", "supro amp", "silvertone amp",
            "gibson amp", "traynor amp", "gretsch amp", "sunn amp", "magnatone amp",
            "selmer amp", "sound city amp", "laney amp", "acoustic amp", "kustom amp",
            
            # Classic amp models
            "fender tweed", "fender blackface", "fender silverface", "fender champ", "fender deluxe",
            "fender twin", "fender princeton", "fender bassman", "fender vibrolux", "fender bandmaster",
            "marshall plexi", "marshall jtm", "marshall jmp", "marshall jcm", "marshall bluesbreaker",
            "vox ac30", "vox ac15", "vox ac10", "vox ac4", "vox cambridge",
            
            # Amp specifications
            "tube amp", "valve amp", "solid state amp", "combo amp", "amp head",
            "speaker cabinet", "amp cabinet", "guitar amplifier", "bass amplifier", "keyboard amplifier",
            "watt amp", "class a amp", "class ab amp", "class d amp", "point to point wiring",
            "handwired amp", "pcb amp", "turret board", "amp circuit", "amp schematic",
            
            # Amp components
            "amp tubes", "preamp tube", "power tube", "rectifier tube", "12ax7 tube",
            "el34 tube", "6l6 tube", "6v6 tube", "el84 tube", "kt88 tube",
            "amp transformer", "output transformer", "power transformer", "amp capacitor", "amp resistor",
            "amp potentiometer", "amp speaker", "alnico speaker", "celestion speaker", "jensen speaker",
            
            # Amp condition and features
            "vintage amp", "original amp", "reissue amp", "amp clone", "amp restoration",
            "amp repair", "amp mod", "amp maintenance", "biased amp", "retubed amp",
            "reverb tank", "spring reverb", "tremolo circuit", "vibrato circuit", "amp footswitch",
            "amp cover", "tolex covering", "tweed covering", "grill cloth", "amp handle"
        ],
        
        "Microphones": [
            # Microphone types
            "condenser microphone", "dynamic microphone", "ribbon microphone", "tube microphone", "usb microphone",
            "large diaphragm", "small diaphragm", "shotgun microphone", "lavalier microphone", "boundary microphone",
            "omnidirectional microphone", "cardioid microphone", "supercardioid microphone", "figure 8 microphone", "multi pattern microphone",
            "vocal microphone", "instrument microphone", "drum microphone", "stereo microphone", "broadcast microphone",
            
            # Microphone brands
            "neumann microphone", "akg microphone", "shure microphone", "sennheiser microphone", "rode microphone",
            "audio technica microphone", "beyerdynamic microphone", "electrovoice microphone", "blue microphone", "audix microphone",
            "telefunken microphone", "royer microphone", "coles microphone", "earthworks microphone", "warm audio microphone",
            "golden age microphone", "cloud microphone", "mojave microphone", "miktek microphone", "avantone microphone",
            
            # Specific microphone models
            "neumann u87", "neumann tlm", "neumann km", "akg c414", "akg c214",
            "shure sm7b", "shure sm57", "shure sm58", "sennheiser md421", "sennheiser e609",
            "rode nt1", "rode nt2", "rode ntk", "blue yeti", "blue bluebird",
            "audio technica at2020", "audio technica at4040", "electrovoice re20", "shure beta", "akg perception",
            
            # Microphone accessories
            "microphone stand", "mic stand", "boom stand", "desktop mic stand", "microphone shock mount",
            "pop filter", "windscreen", "microphone reflection filter", "microphone case", "microphone bag",
            "xlr cable", "microphone preamp", "microphone amplifier", "phantom power", "microphone interface",
            "mic activator", "cloudlifter", "fethead", "microphone pad", "inline pad",
            
            # Microphone terminology
            "mic placement", "recording technique", "proximity effect", "off axis rejection", "phase cancellation",
            "room treatment", "acoustic treatment", "reflection", "reverberation", "signal chain",
            "signal to noise ratio", "self noise", "sensitivity", "frequency response", "transient response",
            "vintage microphone", "classic microphone", "studio microphone", "live microphone", "field recording"
        ],
        
        "DJ Equipment": [
            # DJ controllers and decks
            "dj controller", "dj deck", "turntable", "cdj", "media player",
            "pioneer dj", "pioneer ddj", "pioneer cdj", "pioneer xdj", "rekordbox",
            "denon dj", "denon sc", "denon prime", "traktor controller", "traktor kontrol",
            "numark controller", "numark mixer", "technics turntable", "technics 1200", "direct drive turntable",
            
            # DJ mixers
            "dj mixer", "battle mixer", "club mixer", "four channel mixer", "two channel mixer",
            "pioneer djm", "allen heath xone", "rane mixer", "rane seventy", "denon mixer",
            "mixer effects", "send return", "aux channel", "crossfader", "upfader",
            "eq controls", "filter knob", "mixer isolator", "mixer routing", "mixer output",
            
            # DJ software and digital systems
            "dj software", "serato dj", "traktor pro", "rekordbox dj", "virtual dj",
            "ableton live", "dj control vinyl", "dvs system", "timecode vinyl", "timecode cd",
            "dj mapping", "custom mapping", "dj effects", "dj plugins", "stems",
            "remix deck", "sample deck", "dj loop", "beat grid", "beat sync",
            
            # DJ accessories and equipment
            "dj headphones", "dj needle", "cartridge stylus", "slipmats", "record weight",
            "dj cables", "dj booth", "dj stand", "dj case", "dj bag",
            "dj flight case", "dj coffin", "dj monitor", "booth monitor", "dj lighting",
            "dj microphone", "dj facade", "dj screen", "dj table", "cable management",
            
            # DJ techniques and terminology
            "beatmatching", "scratching", "juggling", "beat juggling", "mixing",
            "crossfading", "cueing", "hot cue", "loop roll", "sampler",
            "back to back", "b2b", "mashup", "remix", "bootleg",
            "beat drop", "breakdown", "buildup", "transition", "turntablism"
        ]
    },
    
    "Tools & DIY": {
        "Power Tools": [
            # Drill types
            "power drill", "cordless drill", "drill driver", "impact driver", "hammer drill",
            "drill press", "right angle drill", "magnetic drill", "rotary hammer", "sds drill",
            "corded drill", "brushless drill", "keyless chuck", "drill bit set", "drill accessories",
            "hex shank", "quick change", "drill clutch", "drill speed", "drill torque",
            
            # Saws
            "circular saw", "miter saw", "table saw", "jigsaw", "reciprocating saw",
            "band saw", "scroll saw", "track saw", "chop saw", "compound miter saw",
            "sliding miter saw", "portable saw", "cordless saw", "corded saw", "trim saw",
            "saw blade", "saw fence", "saw stand", "saw guide", "saw dust collection",
            
            # Sanders and grinders
            "power sander", "random orbit sander", "belt sander", "disc sander", "palm sander",
            "detail sander", "spindle sander", "bench sander", "angle grinder", "bench grinder",
            "die grinder", "surface grinder", "sanding disc", "sanding belt", "sanding pad",
            "sanding sheet", "grinding wheel", "grinding disc", "flap disc", "polishing pad",
            
            # Power tool brands
            "dewalt tools", "milwaukee tools", "makita tools", "bosch tools", "ryobi tools",
            "ridgid tools", "craftsman tools", "hitachi tools", "metabo tools", "festool tools",
            "porter cable", "kobalt tools", "hilti tools", "flex tools", "skil tools",
            "dremel tools", "black and decker", "stanley tools", "worx tools", "hart tools",
            
            # Power tool batteries and features
            "power tool battery", "lithium ion battery", "18v battery", "20v battery", "40v battery",
            "brushless motor", "variable speed", "quick connect", "tool free", "led light",
            "dust collection", "anti vibration", "ergonomic grip", "tool less", "tool lock",
            "cordless tool", "corded tool", "tool combo", "tool kit", "tool set"
        ],
        
        "Hand Tools": [
            # Common hand tools
            "screwdriver set", "wrench set", "pliers set", "hammer", "hand saw",
            "socket set", "ratchet set", "hex key", "allen wrench", "torx bit",
            "utility knife", "chisel set", "file set", "clamp", "level",
            "tape measure", "square", "pry bar", "punch set", "tin snips",
            
            # Screwdrivers
            "phillips screwdriver", "flathead screwdriver", "precision screwdriver", "insulated screwdriver", "multi bit screwdriver",
            "magnetic screwdriver", "ratcheting screwdriver", "screwdriver handle", "screwdriver shaft", "screwdriver grip",
            "stubby screwdriver", "long screwdriver", "impact driver", "manual screwdriver", "jeweler screwdriver",
            "torx screwdriver", "hex screwdriver", "robertson screwdriver", "tri wing", "security bit",
            
            # Wrenches and sockets
            "combination wrench", "adjustable wrench", "crescent wrench", "box wrench", "open end wrench",
            "pipe wrench", "torque wrench", "socket wrench", "ratchet handle", "breaker bar",
            "deep socket", "shallow socket", "impact socket", "universal joint", "extension bar",
            "metric wrench", "sae wrench", "spanner wrench", "monkey wrench", "allen wrench",
            
            # Pliers and cutters
            "needle nose pliers", "slip joint pliers", "channel lock pliers", "vise grip", "locking pliers",
            "diagonal cutter", "wire cutter", "lineman pliers", "end nipper", "crimping tool",
            "wire stripper", "hose clamp pliers", "snap ring pliers", "fencing pliers", "tongue and groove pliers",
            "bent nose pliers", "long nose pliers", "round nose pliers", "side cutter", "flush cutter",
            
            # Measuring and layout tools
            "tape measure", "folding ruler", "laser measure", "digital caliper", "vernier caliper",
            "dial caliper", "micrometer", "combination square", "speed square", "framing square",
            "t square", "try square", "bevel gauge", "protractor", "angle finder",
            "marking gauge", "chalk line", "straight edge", "level", "plumb bob"
        ],
        
        "Welding Equipment": [
            # Welding machine types
            "welding machine", "mig welder", "tig welder", "stick welder", "arc welder",
            "multi process welder", "flux core welder", "spot welder", "engine driven welder", "inverter welder",
            "plasma cutter", "transformer welder", "spool gun", "push pull feeder", "wire feeder",
            "ac welder", "dc welder", "ac/dc welder", "single phase welder", "three phase welder",
            
            # Welding brands
            "lincoln welder", "miller welder", "hobart welder", "esab welder", "everlast welder",
            "fronius welder", "kemppi welder", "eastwood welder", "weldpro welder", "yeswelder",
            "klutch welder", "hitbox welder", "primeweld welder", "lincoln electric", "miller electric",
            "amico welder", "forney welder", "razorweld", "unimig welder", "cigweld",
            
            # Welding accessories
            "welding helmet", "auto darkening helmet", "welding gloves", "welding jacket", "welding apron",
            "welding sleeves", "welding cap", "welding table", "welding clamp", "welding magnets",
            "welding pliers", "welding cart", "welding leads", "ground clamp", "electrode holder",
            "welding blanket", "welding curtain", "welding screen", "welding glasses", "welding respirator",
            
            # Welding consumables
            "welding wire", "flux core wire", "solid wire", "welding electrode", "welding rod",
            "tig filler rod", "tungsten electrode", "tig tungsten", "welding gas", "argon gas",
            "co2 gas", "75/25 gas", "tri mix gas", "gas regulator", "flow meter",
            "welding flux", "welding tip", "contact tip", "gas nozzle", "gas diffuser",
            
            # Welding terminology
            "mig welding", "tig welding", "stick welding", "flux core welding", "arc welding",
            "spot welding", "gas welding", "brazing", "soldering", "cutting",
            "amperage", "voltage", "duty cycle", "polarity", "shielding gas",
            "wire feed speed", "arc length", "weld bead", "weld joint", "weld penetration"
        ],
        
        "Toolboxes": [
            # Toolbox types
            "metal toolbox", "plastic toolbox", "wooden toolbox", "toolbox with drawers", "portable toolbox",
            "rolling toolbox", "mechanic toolbox", "job site box", "tool chest", "top chest",
            "middle chest", "bottom chest", "tool cabinet", "tool storage", "tool cart",
            "stackable toolbox", "modular toolbox", "cantilever toolbox", "truck toolbox", "trailer toolbox",
            
            # Toolbox brands
            "snap on toolbox", "mac tools box", "matco toolbox", "craftsman toolbox", "husky toolbox",
            "milwaukee packout", "dewalt tough system", "ridgid pro tool box", "stanley toolbox", "kobalt toolbox",
            "us general toolbox", "harbor freight toolbox", "kennedy toolbox", "gerstner toolbox", "veto pro pac",
            "keter toolbox", "bosch l-boxx", "makita systainer", "festool systainer", "kaizen foam",
            
            # Toolbox features
            "tool box drawer", "tool box drawer liner", "tool box slide", "tool box hinge", "tool box latch",
            "tool box lock", "tool box handle", "tool box caster", "tool box wheel", "tool box organizer",
            "tool tray", "tool sorter", "socket organizer", "wrench organizer", "screwdriver organizer",
            "tool drawer divider", "tool box foam", "tool box liner", "tool box insert", "tool box divider",
            
            # Portable toolboxes and bags
            "tool bag", "tool tote", "tool backpack", "tool pouch", "tool belt",
            "electrician bag", "plumber bag", "framer bag", "hvac bag", "tech pouch",
            "technician bag", "contractor bag", "jobsite bag", "bucket tool organizer", "tool bucket",
            "open top tool bag", "closed top tool bag", "rolling tool bag", "hard case tool bag", "soft case tool bag"
        ],
        
        "Measuring Devices": [
            # Distance measurement
            "tape measure", "laser measure", "measuring wheel", "digital measure", "folding ruler",
            "measuring tape", "distance meter", "range finder", "sonic measure", "surveyor wheel",
            "yard stick", "meter stick", "telescoping measure", "architect scale", "engineer scale",
            "folding meter", "pocket tape", "chalk line", "laser level", "rotary laser",
            
            # Angle measurement
            "angle finder", "digital angle gauge", "protractor", "bevel gauge", "combination square",
            "speed square", "framing square", "try square", "t bevel", "angle measure",
            "angle cube", "digital protractor", "angle ruler", "miter gauge", "level protractor",
            "magnetic angle finder", "digital level", "inclinometer", "clinometer", "transit level",
            
            # Precision measurement
            "digital caliper", "vernier caliper", "dial caliper", "micrometer", "depth gauge",
            "dial indicator", "feeler gauge", "radius gauge", "thread gauge", "pitch gauge",
            "go no go gauge", "bore gauge", "telescoping gauge", "small hole gauge", "height gauge",
            "digital micrometer", "dial test indicator", "depth micrometer", "inside micrometer", "outside micrometer",
            
            # Level measurement
            "spirit level", "bubble level", "torpedo level", "post level", "line level",
            "i beam level", "box level", "mason level", "digital level", "digital angle level",
            "pocket level", "level tool", "plumb bob", "laser level", "cross line laser",
            "self leveling laser", "multi line laser", "rotary laser level", "dot laser level", "green laser level",
            
            # Environmental measurement
            "moisture meter", "thermal camera", "infrared thermometer", "digital thermometer", "humidity meter",
            "temperature gauge", "pressure gauge", "air quality monitor", "light meter", "sound meter",
            "wind speed meter", "anemometer", "multimeter", "voltage tester", "stud finder",
            "metal detector", "pipe locator", "cable tracer", "magnetic detector", "wall scanner"
        ],
        
        "Woodworking Tools": [
            # Hand tools for woodworking
            "woodworking chisel", "wood chisel set", "mortise chisel", "paring chisel", "bench chisel",
            "hand plane", "jack plane", "block plane", "smoothing plane", "jointer plane",
            "rabbet plane", "shoulder plane", "spokeshave", "card scraper", "cabinet scraper",
            "back saw", "dovetail saw", "tenon saw", "coping saw", "japanese saw",
            
            # Power tools for woodworking
            "table saw", "band saw", "scroll saw", "miter saw", "compound miter saw",
            "sliding miter saw", "track saw", "circular saw", "jigsaw", "reciprocating saw",
            "router", "plunge router", "fixed base router", "trim router", "router table",
            "wood lathe", "bench top lathe", "midi lathe", "mini lathe", "full size lathe",
            
            # Sanders
            "random orbit sander", "palm sander", "belt sander", "disc sander", "spindle sander",
            "benchtop sander", "detail sander", "drum sander", "edge sander", "oscillating sander",
            "hand sanding", "sanding block", "sanding disc", "sanding belt", "sanding spindle",
            "sandpaper", "sanding sheet", "sanding pad", "sanding screen", "sanding sponge",
            
            # Joinery and shaping
            "biscuit joiner", "domino joiner", "doweling jig", "pocket hole jig", "dovetail jig",
            "mortiser", "benchtop mortiser", "hollow chisel mortiser", "tenon jig", "box joint jig",
            "router bit", "router table", "router fence", "dovetail bit", "roundover bit",
            "flush trim bit", "straight bit", "chamfer bit", "v groove bit", "panel raising bit",
            
            # Workshop accessories
            "workbench", "woodworking bench", "bench vise", "bench dog", "bench hook",
            "clamp", "bar clamp", "pipe clamp", "quick clamp", "corner clamp",
            "wood glue", "wood finish", "wood stain", "woodworking plan", "wood joint",
            "dust collection", "dust collector", "wood chisel", "sharpening stone", "marking gauge"
        ]
    },
    
    "Outdoors & Sports": {
        "Bikes": [
            # Bike types
            "mountain bike", "road bike", "hybrid bike", "gravel bike", "cruiser bike",
            "bmx bike", "folding bike", "electric bike", "fat bike", "touring bike",
            "commuter bike", "fixed gear bike", "single speed bike", "triathlon bike", "cyclocross bike",
            "downhill bike", "dirt jumper", "enduro bike", "trail bike", "xc bike",
            
            # Bike brands
            "trek bike", "specialized bike", "giant bike", "cannondale bike", "santa cruz bike",
            "schwinn bike", "diamondback bike", "fuji bike", "bianchi bike", "cervelo bike",
            "gt bike", "kona bike", "marin bike", "norco bike", "pivot bike",
            "salsa bike", "surly bike", "yeti bike", "canyon bike", "colnago bike",
            
            # Bike components
            "bike frame", "bike fork", "bike wheel", "bike tire", "bike tube",
            "bike handlebar", "bike stem", "bike seatpost", "bike saddle", "bike pedal",
            "bike chain", "bike cassette", "bike crankset", "bike derailleur", "bike shifter",
            "bike brake", "bike disc brake", "bike hub", "bike spoke", "bike rim",
            
            # Bike accessories
            "bike helmet", "bike lock", "bike light", "bike pump", "bike computer",
            "bike rack", "bike bag", "bike basket", "bike fender", "bike mirror",
            "bike water bottle", "bike cage", "bike stand", "bike repair stand", "bike repair kit",
            "bike multi tool", "bike chain tool", "bike lock mount", "bike phone mount", "bike gopro mount",
            
            # Bike clothing and gear
            "cycling jersey", "cycling shorts", "cycling bibs", "cycling tights", "cycling jacket",
            "cycling gloves", "cycling shoes", "cycling socks", "cycling cap", "cycling glasses",
            "cycling sunglasses", "chamois cream", "cycling underwear", "cycling base layer", "cycling vest",
            "cycling rain gear", "bike cleats", "cycling shoe covers", "arm warmers", "leg warmers"
        ],
        
        "Skateboards": [
            # Skateboard types
            "skateboard", "longboard", "cruiser skateboard", "penny board", "electric skateboard",
            "old school skateboard", "street skateboard", "park skateboard", "vert skateboard", "pool skateboard",
            "mini cruiser", "drop through longboard", "pintail longboard", "dancing longboard", "downhill longboard",
            "freeride longboard", "carving longboard", "freestyle skateboard", "tech skateboard", "transition skateboard",
            
            # Skateboard components
            "skateboard deck", "skateboard truck", "skateboard wheel", "skateboard bearing", "skateboard grip tape",
            "skateboard hardware", "skateboard riser", "skateboard rail", "skateboard nose", "skateboard tail",
            "longboard deck", "longboard truck", "longboard wheel", "longboard bearing", "longboard grip tape",
            "skateboard complete", "longboard complete", "cruiser complete", "skateboard kit", "build your own skateboard",
            
            # Skateboard brands
            "element skateboard", "baker skateboard", "santa cruz skateboard", "powell peralta skateboard", "blind skateboard",
            "zero skateboard", "toy machine skateboard", "girl skateboard", "chocolate skateboard", "flip skateboard",
            "alien workshop skateboard", "real skateboard", "anti hero skateboard", "almost skateboard", "dgk skateboard",
            "enjoi skateboard", "primitive skateboard", "plan b skateboard", "darkstar skateboard", "deathwish skateboard",
            
            # Longboard brands
            "sector 9 longboard", "loaded longboard", "landyachtz longboard", "arbor longboard", "rayne longboard",
            "madrid longboard", "pantheon longboard", "moonshine longboard", "bustin longboard", "db longboard",
            "dusters longboard", "earthwing longboard", "gravity longboard", "never summer longboard", "original longboard",
            "omen longboard", "zenit longboard", "hamboards longboard", "prism longboard", "carmen longboard",
            
            # Skateboarding gear and accessories
            "skate shoe", "skate helmet", "skate pad", "knee pad", "elbow pad",
            "wrist guard", "skate tool", "skate wax", "skate backpack", "skate bag",
            "skate rack", "skate storage", "skate leash", "skate grip", "skate cleaner",
            "skate video", "skate magazine", "skate shop", "skate park", "skate spot"
        ],
        
        "Scooters": [
            # Scooter types
            "kick scooter", "pro scooter", "stunt scooter", "electric scooter", "folding scooter",
            "adult scooter", "kids scooter", "commuter scooter", "three wheel scooter", "off road scooter",
            "freestyle scooter", "trick scooter", "push scooter", "mobility scooter", "vespa scooter",
            "motor scooter", "gas scooter", "seated scooter", "foldable scooter", "portable scooter",
            
            # Stunt scooter components
            "scooter deck", "scooter bar", "scooter wheel", "scooter fork", "scooter clamp",
            "scooter grip", "scooter brake", "scooter headset", "scooter bearing", "scooter spacer",
            "scooter compression", "scs clamp", "hic compression", "ihc compression", "scooter peg",
            "scooter standoff", "scooter hub", "scooter core", "scooter complete", "custom scooter",
            
            # Scooter brands
            "razor scooter", "micro scooter", "xiaomi scooter", "segway scooter", "ninebot scooter",
            "envy scooter", "lucky scooter", "tilt scooter", "ethic scooter", "aztec scooter",
            "native scooter", "flavor scooter", "root scooter", "district scooter", "phoenix scooter",
            "proto scooter", "ao scooter", "mgp scooter", "madd gear scooter", "fuzion scooter",
            
            # Electric scooter features
            "electric scooter battery", "electric scooter motor", "electric scooter range", "electric scooter speed",
            "electric scooter charger", "electric scooter controller", "electric scooter display", "electric scooter light",
            "electric scooter suspension", "electric scooter brake", "electric scooter tire", "electric scooter tube",
            "electric scooter throttle", "electric scooter app", "electric scooter lock", "electric scooter alarm",
            
            # Scooter accessories and gear
            "scooter helmet", "scooter pad", "scooter glove", "scooter bag", "scooter stand",
            "scooter rack", "scooter hanger", "scooter lock", "scooter light", "scooter bell",
            "scooter basket", "scooter phone mount", "scooter repair kit", "scooter tool", "scooter maintenance",
            "scooter lubricant", "scooter cleaner", "scooter cover", "scooter storage", "scooter transportation"
        ],
        
        "Camping Gear": [
            # Shelter
            "camping tent", "backpacking tent", "family tent", "instant tent", "pop up tent",
            "dome tent", "cabin tent", "ultralight tent", "tarp tent", "hammock tent",
            "tent footprint", "tent stakes", "tent poles", "tent rainfly", "tent vestibule",
            "tarp shelter", "bivy sack", "camping hammock", "camping cot", "sleeping pad",
            
            # Sleeping
            "sleeping bag", "camping quilt", "mummy bag", "rectangular bag", "double sleeping bag",
            "down sleeping bag", "synthetic sleeping bag", "sleeping bag liner", "compression sack", "stuff sack",
            "air mattress", "sleeping pad", "self inflating pad", "foam pad", "inflatable pillow",
            "camping pillow", "sleeping bag hood", "camp bedding", "camping blanket", "emergency blanket",
            
            # Cooking
            "camping stove", "backpacking stove", "camp grill", "camp chef", "portable stove",
            "propane stove", "butane stove", "alcohol stove", "wood burning stove", "dual fuel stove",
            "camp cookware", "mess kit", "cooking pot", "frying pan", "camping kettle",
            "camping utensils", "camping dishes", "camping mug", "camping plate", "camping bowl",
            
            # Packs and storage
            "hiking backpack", "camping backpack", "internal frame pack", "external frame pack", "frameless pack",
            "day pack", "hydration pack", "dry bag", "stuff sack", "compression sack",
            "bear canister", "food storage", "bear bag", "camping box", "gear organizer",
            "pack cover", "pack liner", "waterproof bag", "roll top bag", "camping duffel",
            
            # Accessories and tools
            "camping knife", "multi tool", "hiking pole", "trekking pole", "camp axe",
            "camping saw", "paracord", "tent repair kit", "first aid kit", "emergency kit",
            "headlamp", "camping lantern", "flashlight", "camp light", "rechargeable light",
            "compass", "gps device", "map case", "survival gear", "emergency shelter"
        ],
        
        "Hiking Gear": [
            # Footwear
            "hiking boots", "hiking shoes", "trail runners", "approach shoes", "mountaineering boots",
            "waterproof boots", "waterproof shoes", "hiking sandals", "trekking shoes", "outdoor shoes",
            "boot insole", "hiking sock", "wool sock", "sock liner", "gaiters",
            "boot laces", "boot care", "waterproofing spray", "boot wax", "boot conditioner",
            
            # Clothing
            "hiking pants", "hiking shorts", "convertible pants", "hiking shirt", "base layer",
            "hiking jacket", "rain jacket", "softshell jacket", "hardshell jacket", "down jacket",
            "fleece jacket", "insulated jacket", "hiking underwear", "hiking bra", "hiking hat",
            "sun hat", "beanie", "buff headwear", "neck gaiter", "hiking gloves",
            
            # Packs
            "day pack", "hiking backpack", "trekking pack", "ultralight pack", "frame pack",
            "hip pack", "fanny pack", "waist pack", "hydration pack", "hydration bladder",
            "water bottle", "water filter", "water purifier", "gravity filter", "bottle filter",
            "pack rain cover", "pack liner", "pack organizer", "compression strap", "load lifter",
            
            # Accessories
            "trekking pole", "hiking pole", "walking stick", "monopod", "camera tripod",
            "hiking gps", "handheld gps", "outdoor watch", "altimeter", "compass",
            "topographic map", "trail map", "guidebook", "map case", "waterproof map",
            "binoculars", "monocular", "spotting scope", "field guide", "nature guide",
            
            # Safety and protection
            "hiking first aid", "blister kit", "moleskin", "insect repellent", "tick remover",
            "bear spray", "bear bell", "emergency whistle", "signal mirror", "emergency blanket",
            "sunscreen", "lip balm", "sun protection", "sun shirt", "sun gloves",
            "rain cover", "pack cover", "dry bag", "waterproof case", "waterproof pouch"
        ],
        
        "Fishing Gear": [
            # Rods
            "fishing rod", "spinning rod", "baitcasting rod", "fly rod", "ice fishing rod",
            "telescopic rod", "travel rod", "ultralight rod", "medium rod", "heavy rod",
            "surf rod", "offshore rod", "trolling rod", "jigging rod", "crappie rod",
            "bass rod", "trout rod", "salmon rod", "catfish rod", "musky rod",
            
            # Reels
            "fishing reel", "spinning reel", "baitcasting reel", "fly reel", "spincast reel",
            "conventional reel", "trolling reel", "centerpin reel", "surf reel", "offshore reel",
            "level wind reel", "inline reel", "underspin reel", "baitrunner reel", "low profile reel",
            "high speed reel", "ultralight reel", "saltwater reel", "freshwater reel", "ice fishing reel",
            
            # Terminal tackle
            "fishing hook", "circle hook", "j hook", "treble hook", "octopus hook",
            "fishing weight", "split shot", "drop shot", "bullet weight", "egg sinker",
            "fishing swivel", "snap swivel", "barrel swivel", "three way swivel", "fishing snap",
            "fishing line", "monofilament line", "fluorocarbon line", "braided line", "fly line",
            
            # Lures and bait
            "fishing lure", "spinner bait", "crank bait", "jig", "soft plastic",
            "topwater lure", "jerkbait", "stickbait", "popper", "buzzbait",
            "chatterbait", "spinnerbait", "swimbait", "spoon", "inline spinner",
            "trolling lure", "fly", "dry fly", "wet fly", "streamer fly",
            
            # Accessories
            "fishing pliers", "hook remover", "fish gripper", "landing net", "fishing gaff",
            "tackle box", "fishing bag", "rod holder", "rod rack", "fishing vest",
            "fishing waders", "fishing boots", "fishing rain gear", "fishing hat", "polarized sunglasses",
            "fish finder", "fishing electronics", "fishing scale", "fish ruler", "fillet knife"
        ],
        
        "Snowboards": [
            # Snowboard types
            "all mountain snowboard", "freestyle snowboard", "freeride snowboard", "powder snowboard", "park snowboard",
            "directional snowboard", "twin tip snowboard", "true twin snowboard", "directional twin snowboard", "tapered snowboard",
            "camber snowboard", "rocker snowboard", "hybrid camber", "flat snowboard", "volume shifted snowboard",
            "men's snowboard", "women's snowboard", "kids snowboard", "beginner snowboard", "intermediate snowboard",
            
            # Snowboard brands
            "burton snowboard", "lib tech snowboard", "gnu snowboard", "arbor snowboard", "jones snowboard",
            "k2 snowboard", "ride snowboard", "capita snowboard", "never summer snowboard", "rome snowboard",
            "salomon snowboard", "rossignol snowboard", "nitro snowboard", "dc snowboard", "yes snowboard",
            "gnu board", "mervin board", "bataleon board", "endeavor board", "academy board",
            
            # Snowboard bindings
            "snowboard binding", "burton binding", "union binding", "rome binding", "flux binding",
            "now binding", "k2 binding", "ride binding", "salomon binding", "nitro binding",
            "strap binding", "rear entry binding", "step on binding", "split board binding", "binding baseplate",
            "binding highback", "binding strap", "binding ratchet", "binding disc", "binding hardware",
            
            # Snowboard boots
            "snowboard boot", "snowboard shoe", "burton boot", "thirty two boot", "dc boot",
            "vans boot", "k2 boot", "ride boot", "nitro boot", "salomon boot",
            "traditional lace boot", "boa boot", "dual boa boot", "speed lace boot", "therm ic boot",
            "stiff boot", "medium flex boot", "soft boot", "snowboard liner", "boot heat mold",
            
            # Snowboard gear and accessories
            "snowboard jacket", "snowboard pants", "snowboard bib", "snowboard helmet", "snowboard goggles",
            "snowboard gloves", "snowboard mittens", "snowboard backpack", "snowboard stomp pad", "snowboard leash",
            "snowboard socks", "base layer", "snowboard wax", "waxing iron", "edge tuner",
            "snowboard bag", "snowboard lock", "roof rack", "impact shorts", "snowboard tool"
        ]
    }
}

def get_keywords_for_subcategory(subcategory):
    """
    Get a list of keywords for a specific subcategory.
    
    Args:
        subcategory (str): The subcategory to get keywords for
        
    Returns:
        list: A list of keywords for the subcategory, or an empty list if not found
    """
    for category, subcats in COMPREHENSIVE_KEYWORDS.items():
        if subcategory in subcats:
            return subcats[subcategory]
    return []

def generate_keywords(subcategory, include_variations=True, max_keywords=20):
    """
    Generate a list of keywords for a subcategory, optionally with variations.
    
    Args:
        subcategory (str): The subcategory to generate keywords for
        include_variations (bool): Whether to include common typos and variations
        max_keywords (int): Maximum number of keywords to return
        
    Returns:
        list: A list of keywords for the subcategory
    """
    if not subcategory:
        return []
        
    keywords = get_keywords_for_subcategory(subcategory)
    
    # If subcategory not found, return the subcategory itself as a keyword
    if not keywords:
        return [subcategory.lower()]
    
    # If variations not needed, return original keywords up to max_keywords
    if not include_variations:
        return keywords[:max_keywords]
    
    # Add common typos and variations based on existing keywords
    expanded_keywords = []
    for keyword in keywords[:max_keywords//2]:  # Use half the slots for original keywords
        expanded_keywords.append(keyword)
        
        # Add typo variations for keywords that are long enough
        if len(keyword) > 3:
            # Swap adjacent characters
            for i in range(len(keyword) - 1):
                if keyword[i].isalpha() and keyword[i+1].isalpha():
                    typo = keyword[:i] + keyword[i+1] + keyword[i] + keyword[i+2:]
                    expanded_keywords.append(typo)
                    
            # Missing characters
            for i in range(1, len(keyword) - 1):
                if keyword[i].isalpha():
                    typo = keyword[:i] + keyword[i+1:]
                    expanded_keywords.append(typo)
    
    # Remove duplicates and limit to max_keywords
    return list(dict.fromkeys(expanded_keywords))[:max_keywords]
