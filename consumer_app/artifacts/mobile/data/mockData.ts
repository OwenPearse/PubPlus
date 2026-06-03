export type MealDeal = "Parma Night" | "Burger Night" | "Steak Night" | "Taco Night" | "Pizza Night";

export type Special = {
  id: string;
  title: string;
  description: string;
  validUntil: string;
};

export type Event = {
  id: string;
  title: string;
  date: string;
  time: string;
  description: string;
};

export type MenuItem = {
  category: string;
  items: { name: string; price: string; description?: string }[];
};

export type OpeningHours = {
  Mon: string;
  Tue: string;
  Wed: string;
  Thu: string;
  Fri: string;
  Sat: string;
  Sun: string;
};

export type Venue = {
  id: string;
  name: string;
  suburb: string;
  address: string;
  type: "pub" | "bar" | "rooftop" | "sports bar" | "craft beer";
  isOpen: boolean;
  closingTime: string;
  rating: number;
  reviewCount: number;
  tapBeers: string[];
  specials: Special[];
  events: Event[];
  features: string[];
  description: string;
  imageColor: string;
  latitude: number;
  longitude: number;
  mealDeal?: MealDeal;
  isSaved?: boolean;
  phone?: string;
  website?: string;
  openingHours: OpeningHours;
  happyHour?: { days: string; times: string; deal: string };
  menuItems?: MenuItem[];
};

/** Demo/legacy suburb labels only — not used for Search or Profile pickers (use reference localities). */
export const SUBURBS = [
  "Fitzroy",
  "Carlton",
  "Richmond",
  "Brunswick",
  "South Yarra",
  "CBD",
  "Collingwood",
  "Northcote",
  "Prahran",
  "St Kilda",
  "Windsor",
  "Abbotsford",
  "Hawthorn",
  "Cremorne",
  "Port Melbourne",
];

/** Approximate suburb centroids for Search radius (WGS84). Aligns with Melbourne dev seed localities. */
export const SUBURB_ORIGIN_COORDINATES: Record<
  string,
  { lat: number; lng: number }
> = {
  Abbotsford: { lat: -37.801, lng: 144.993 },
  Brunswick: { lat: -37.77, lng: 144.96 },
  Carlton: { lat: -37.8, lng: 144.967 },
  CBD: { lat: -37.8136, lng: 144.9631 },
  Collingwood: { lat: -37.802, lng: 144.984 },
  Cremorne: { lat: -37.826, lng: 144.995 },
  Fitzroy: { lat: -37.798, lng: 144.978 },
  Hawthorn: { lat: -37.822, lng: 145.028 },
  "Northcote": { lat: -37.769, lng: 144.999 },
  "Port Melbourne": { lat: -37.84, lng: 144.942 },
  Prahran: { lat: -37.851, lng: 144.993 },
  Richmond: { lat: -37.818, lng: 145.001 },
  "South Yarra": { lat: -37.838, lng: 144.992 },
  "St Kilda": { lat: -37.868, lng: 144.981 },
  Windsor: { lat: -37.856, lng: 144.992 },
};

export const MEAL_SPECIALS: MealDeal[] = [
  "Parma Night",
  "Burger Night",
  "Steak Night",
  "Taco Night",
  "Pizza Night",
];

export const VENUES: Venue[] = [
  {
    id: "1",
    name: "The Builders Arms",
    suburb: "Fitzroy",
    address: "211 Gertrude St, Fitzroy",
    type: "pub",
    isOpen: true,
    closingTime: "1:00 AM",
    rating: 4.5,
    reviewCount: 312,
    phone: "(03) 9419 0818",
    website: "buildersarmsfitzroy.com.au",
    tapBeers: ["Mountain Goat Hazy IPA", "Coopers Pale", "Young Henrys Natural", "Carlton Draught"],
    specials: [
      {
        id: "s1",
        title: "Parma Night",
        description: "$20 parma + pint every Wednesday",
        validUntil: "Wednesday 9pm",
      },
      {
        id: "s2",
        title: "Happy Hour",
        description: "$6 house beers 4–6pm daily",
        validUntil: "Daily 4–6pm",
      },
    ],
    events: [
      {
        id: "e1",
        title: "Trivia Night",
        date: "Tonight",
        time: "7:30 PM",
        description: "Teams of up to 6. $5 entry, prizes for top 3.",
      },
    ],
    features: ["Beer Garden", "Live Music", "Pool Table", "Dog Friendly"],
    description:
      "A Fitzroy institution since 1853. Warm, unpretentious, and always packed on a Friday.",
    imageColor: "#8B4513",
    latitude: -37.8038,
    longitude: 144.9777,
    mealDeal: "Parma Night",
    openingHours: {
      Mon: "12:00 PM – 11:00 PM",
      Tue: "12:00 PM – 11:00 PM",
      Wed: "12:00 PM – 11:00 PM",
      Thu: "12:00 PM – 12:00 AM",
      Fri: "12:00 PM – 1:00 AM",
      Sat: "11:00 AM – 1:00 AM",
      Sun: "11:00 AM – 10:00 PM",
    },
    happyHour: {
      days: "Daily",
      times: "4:00 PM – 6:00 PM",
      deal: "$6 house beers, $8 house wines & spirits",
    },
    menuItems: [
      {
        category: "Pub Classics",
        items: [
          { name: "Chicken Parma", price: "$20", description: "Napoli, leg ham, mozzarella, chips & salad" },
          { name: "Beef Burger", price: "$18", description: "Angus patty, pickles, American cheese, house sauce" },
          { name: "Fish & Chips", price: "$19", description: "Beer-battered flathead, tartare, lemon" },
          { name: "Pot Pie", price: "$21", description: "Slow-cooked beef & Guinness, shortcrust pastry" },
        ],
      },
      {
        category: "Snacks",
        items: [
          { name: "Loaded Fries", price: "$12", description: "Cheese sauce, bacon, jalapeños, sour cream" },
          { name: "Wings (6 pcs)", price: "$14", description: "Buffalo or honey soy, blue cheese dip" },
          { name: "Arancini (4 pcs)", price: "$13", description: "Mushroom & truffle, aioli" },
        ],
      },
    ],
  },
  {
    id: "2",
    name: "Rooftop Bar",
    suburb: "CBD",
    address: "252 Swanston St, Melbourne",
    type: "rooftop",
    isOpen: true,
    closingTime: "11:00 PM",
    rating: 4.3,
    reviewCount: 892,
    phone: "(03) 9654 5394",
    website: "rooftopbar.com.au",
    tapBeers: ["Stone & Wood Pacific Ale", "4 Pines Kolsch", "Balter XPA", "Heineken"],
    specials: [
      {
        id: "s3",
        title: "Sundowner Special",
        description: "$9 cocktails during golden hour 5–7pm",
        validUntil: "Daily 5–7pm",
      },
    ],
    events: [
      {
        id: "e2",
        title: "Live DJ",
        date: "Tonight",
        time: "8:00 PM",
        description: "DJ sets from Melbourne's best selectors every Friday.",
      },
    ],
    features: ["Rooftop", "City Views", "Cocktails", "Heated"],
    description:
      "Sweeping 360° views of Melbourne CBD from the top of Curtin House. The city's most iconic perch.",
    imageColor: "#1a3a5c",
    latitude: -37.8124,
    longitude: 144.9656,
    openingHours: {
      Mon: "Closed",
      Tue: "Closed",
      Wed: "5:00 PM – 11:00 PM",
      Thu: "5:00 PM – 11:00 PM",
      Fri: "5:00 PM – 11:00 PM",
      Sat: "2:00 PM – 11:00 PM",
      Sun: "2:00 PM – 9:00 PM",
    },
    happyHour: {
      days: "Wed – Fri",
      times: "5:00 PM – 7:00 PM",
      deal: "$9 cocktails, $7 house wine & beer",
    },
    menuItems: [
      {
        category: "Cocktails",
        items: [
          { name: "Aperol Spritz", price: "$16" },
          { name: "Negroni", price: "$17" },
          { name: "Espresso Martini", price: "$17" },
          { name: "Margarita", price: "$16" },
        ],
      },
      {
        category: "Bar Snacks",
        items: [
          { name: "Charcuterie Board", price: "$28", description: "Cured meats, pickles, sourdough" },
          { name: "Truffle Fries", price: "$14", description: "Parmesan, house mayo" },
          { name: "Oysters (6)", price: "$24", description: "Natural or Kilpatrick" },
        ],
      },
    ],
  },
  {
    id: "3",
    name: "Local Taphouse",
    suburb: "South Yarra",
    address: "184 Chapel St, South Yarra",
    type: "craft beer",
    isOpen: true,
    closingTime: "12:00 AM",
    rating: 4.7,
    reviewCount: 540,
    phone: "(03) 9804 6666",
    website: "thelocal.com.au",
    tapBeers: [
      "Feral Hop Hog",
      "Pirate Life Throwback IPA",
      "BrewDog Punk IPA",
      "Bright Pale Ale",
      "Moon Dog Lager",
      "Fixation Brewing IPA",
    ],
    specials: [
      {
        id: "s4",
        title: "Craft Flight",
        description: "Any 4 tasting paddles for $22",
        validUntil: "All week",
      },
    ],
    events: [],
    features: ["30+ Taps", "Craft Beer", "Bar Snacks", "Knowledgeable Staff"],
    description:
      "Melbourne's premier craft beer destination with 40 rotating taps. Staff actually know their stuff.",
    imageColor: "#2d5a1b",
    latitude: -37.8398,
    longitude: 144.9941,
    openingHours: {
      Mon: "3:00 PM – 11:00 PM",
      Tue: "3:00 PM – 11:00 PM",
      Wed: "3:00 PM – 11:00 PM",
      Thu: "3:00 PM – 12:00 AM",
      Fri: "12:00 PM – 12:00 AM",
      Sat: "12:00 PM – 12:00 AM",
      Sun: "12:00 PM – 10:00 PM",
    },
    happyHour: {
      days: "Mon – Fri",
      times: "3:00 PM – 5:00 PM",
      deal: "$2 off all tap beers, any 4 tasting paddles $22",
    },
    menuItems: [
      {
        category: "Bar Food",
        items: [
          { name: "Beer Brats", price: "$16", description: "Bratwurst, sauerkraut, mustard, pretzel bun" },
          { name: "Bavarian Pretzel", price: "$10", description: "Butter, grain mustard" },
          { name: "Cheese Board", price: "$22", description: "Selection of 3, crackers, quince" },
          { name: "Pulled Pork Slider (2)", price: "$14", description: "Slow cooked, apple slaw" },
        ],
      },
    ],
  },
  {
    id: "4",
    name: "The Retreat Hotel",
    suburb: "Brunswick",
    address: "280 Sydney Rd, Brunswick",
    type: "pub",
    isOpen: true,
    closingTime: "1:00 AM",
    rating: 4.4,
    reviewCount: 276,
    phone: "(03) 9380 4090",
    website: "retreathotel.com.au",
    tapBeers: ["Hawkers IPA", "Moon Dog Fizzer", "Carlton Draught", "Coopers Green"],
    specials: [
      {
        id: "s5",
        title: "Live Music Free Entry",
        description: "No cover charge for all live acts this week",
        validUntil: "This week",
      },
    ],
    events: [
      {
        id: "e3",
        title: "Live Music: The Riff Brothers",
        date: "Tonight",
        time: "9:00 PM",
        description: "Blues and rock covers from Melbourne legends.",
      },
      {
        id: "e4",
        title: "Open Mic Night",
        date: "Tuesday",
        time: "7:00 PM",
        description: "Sign up at 6:30pm. All welcome.",
      },
    ],
    features: ["Live Music", "Beer Garden", "Vegan Options", "Live Sport"],
    description:
      "The beating heart of Brunswick's live music scene. Three nights of live music every week.",
    imageColor: "#5c1a5c",
    latitude: -37.7664,
    longitude: 144.9611,
    openingHours: {
      Mon: "4:00 PM – 11:00 PM",
      Tue: "4:00 PM – 12:00 AM",
      Wed: "4:00 PM – 12:00 AM",
      Thu: "4:00 PM – 1:00 AM",
      Fri: "12:00 PM – 1:00 AM",
      Sat: "12:00 PM – 1:00 AM",
      Sun: "12:00 PM – 10:00 PM",
    },
    happyHour: {
      days: "Mon – Thu",
      times: "4:00 PM – 6:00 PM",
      deal: "$5.50 schooners, $7 house wine",
    },
    menuItems: [
      {
        category: "Mains",
        items: [
          { name: "Chicken Parma", price: "$19", description: "Classic with chips & salad" },
          { name: "Mushroom Risotto (V)", price: "$18", description: "Porcini, parmesan, truffle oil" },
          { name: "Beef Brisket", price: "$22", description: "12hr smoked, pickled slaw, cornbread" },
        ],
      },
      {
        category: "Vegan Specials",
        items: [
          { name: "Vegan Burger", price: "$17", description: "Beyond patty, vegan cheese, sriracha slaw" },
          { name: "Cauliflower Wings (6)", price: "$13", description: "Buffalo sauce, ranch dip" },
        ],
      },
    ],
  },
  {
    id: "5",
    name: "Jimmy's on Collins",
    suburb: "CBD",
    address: "50 Collins St, Melbourne",
    type: "bar",
    isOpen: false,
    closingTime: "Opens 4pm",
    rating: 4.2,
    reviewCount: 189,
    phone: "(03) 9650 2123",
    website: "jimmysoncollins.com.au",
    tapBeers: ["Asahi", "Peroni", "Balter Cerveza", "Hawkers Corridor"],
    specials: [
      {
        id: "s6",
        title: "After Work Pack",
        description: "$45 for a jug and a pizza, Mon–Fri 4–7pm",
        validUntil: "Mon–Fri 4–7pm",
      },
    ],
    events: [],
    features: ["Cocktails", "Wine Bar", "Snacks", "Private Hire"],
    description:
      "Sophisticated after-work bar in the heart of Collins St's legal precinct.",
    imageColor: "#2c3e50",
    latitude: -37.8149,
    longitude: 144.9668,
    mealDeal: "Pizza Night",
    openingHours: {
      Mon: "4:00 PM – 11:00 PM",
      Tue: "4:00 PM – 11:00 PM",
      Wed: "4:00 PM – 11:00 PM",
      Thu: "4:00 PM – 12:00 AM",
      Fri: "4:00 PM – 12:00 AM",
      Sat: "5:00 PM – 12:00 AM",
      Sun: "Closed",
    },
    happyHour: {
      days: "Mon – Fri",
      times: "4:00 PM – 6:00 PM",
      deal: "$10 house cocktails, $8 beers, $9 wines",
    },
    menuItems: [
      {
        category: "Pizzas",
        items: [
          { name: "Margherita", price: "$18", description: "San Marzano, fior di latte, basil" },
          { name: "Prosciutto & Rocket", price: "$22", description: "Mozzarella, parmesan, lemon oil" },
          { name: "Truffle & Mushroom", price: "$23", description: "White base, wild mushrooms, truffle oil" },
        ],
      },
      {
        category: "Small Plates",
        items: [
          { name: "Burrata", price: "$17", description: "Heirloom tomato, basil oil, sea salt" },
          { name: "Salumi Board", price: "$24", description: "Prosciutto, salami, pickles, grissini" },
        ],
      },
    ],
  },
  {
    id: "6",
    name: "The Corner Hotel",
    suburb: "Richmond",
    address: "57 Swan St, Richmond",
    type: "pub",
    isOpen: true,
    closingTime: "3:00 AM",
    rating: 4.6,
    reviewCount: 1204,
    phone: "(03) 9427 9198",
    website: "cornerhotel.com",
    tapBeers: ["Little Creatures", "Stone & Wood", "Furphy", "Carlton Draught", "VB"],
    specials: [
      {
        id: "s7",
        title: "Pre-show Special",
        description: "$8 schooners before 8pm on gig nights",
        validUntil: "Gig nights before 8pm",
      },
    ],
    events: [
      {
        id: "e5",
        title: "Sports Screening: AFL Finals",
        date: "Tonight",
        time: "7:25 PM",
        description: "Richmond vs Collingwood. Every screen live.",
      },
    ],
    features: ["Live Venue", "Beer Garden", "Sports Screens", "Late Night"],
    description:
      "Melbourne's most beloved live music venue. Two stages, a legendary front bar, and great beer.",
    imageColor: "#8B0000",
    latitude: -37.8254,
    longitude: 144.9988,
    openingHours: {
      Mon: "12:00 PM – 1:00 AM",
      Tue: "12:00 PM – 1:00 AM",
      Wed: "12:00 PM – 1:00 AM",
      Thu: "12:00 PM – 3:00 AM",
      Fri: "12:00 PM – 3:00 AM",
      Sat: "12:00 PM – 3:00 AM",
      Sun: "12:00 PM – 1:00 AM",
    },
    happyHour: {
      days: "Mon – Fri",
      times: "4:00 PM – 6:00 PM",
      deal: "$6 schooners, $8 house spirits",
    },
    menuItems: [
      {
        category: "Pub Food",
        items: [
          { name: "Chicken Parma", price: "$21", description: "Napoli, leg ham, cheese, chips & salad" },
          { name: "Steak Sandwich", price: "$19", description: "150g scotch, caramelised onion, aioli" },
          { name: "Nachos", price: "$15", description: "Cheese, jalapeños, sour cream, salsa, guac" },
          { name: "Loaded Fries", price: "$12", description: "Cheese sauce, bacon bits, spring onion" },
        ],
      },
    ],
  },
  {
    id: "7",
    name: "Union Hotel",
    suburb: "Carlton",
    address: "229 Faraday St, Carlton",
    type: "pub",
    isOpen: true,
    closingTime: "11:00 PM",
    rating: 4.3,
    reviewCount: 223,
    phone: "(03) 9347 1222",
    website: "unionhotelcarlton.com.au",
    tapBeers: ["Coopers Pale", "James Squire", "Carlton Draught", "Great Northern"],
    specials: [
      {
        id: "s8",
        title: "Student Night",
        description: "$5 beers all night with student ID, Thursdays",
        validUntil: "Thursdays",
      },
    ],
    events: [
      {
        id: "e6",
        title: "Pub Quiz",
        date: "Tonight",
        time: "7:00 PM",
        description: "The weekly quiz. Book a table online.",
      },
    ],
    features: ["Pub Quiz", "Pool Table", "Student Friendly", "Beer Garden"],
    description:
      "Carlton's neighbourhood pub. Unpretentious, welcoming, and right near the uni.",
    imageColor: "#2d4a1b",
    latitude: -37.7991,
    longitude: 144.9672,
    mealDeal: "Burger Night",
    openingHours: {
      Mon: "11:00 AM – 11:00 PM",
      Tue: "11:00 AM – 11:00 PM",
      Wed: "11:00 AM – 11:00 PM",
      Thu: "11:00 AM – 12:00 AM",
      Fri: "11:00 AM – 12:00 AM",
      Sat: "11:00 AM – 12:00 AM",
      Sun: "11:00 AM – 10:00 PM",
    },
    happyHour: {
      days: "Mon – Fri",
      times: "4:00 PM – 6:00 PM",
      deal: "$5 schooners, $6 house wine",
    },
    menuItems: [
      {
        category: "Burgers",
        items: [
          { name: "Classic Cheeseburger", price: "$17", description: "Double patty, American cheese, pickles, mustard" },
          { name: "Crispy Chicken Burger", price: "$18", description: "Buttermilk fried, slaw, hot sauce mayo" },
          { name: "Mushroom Swiss (V)", price: "$16", description: "Portobello, Swiss, truffle mayo" },
        ],
      },
      {
        category: "Sides",
        items: [
          { name: "Shoestring Fries", price: "$8" },
          { name: "Sweet Potato Fries", price: "$9" },
          { name: "Onion Rings", price: "$8" },
        ],
      },
    ],
  },
  {
    id: "8",
    name: "Naked for Satan",
    suburb: "Fitzroy",
    address: "285 Brunswick St, Fitzroy",
    type: "bar",
    isOpen: true,
    closingTime: "1:00 AM",
    rating: 4.5,
    reviewCount: 678,
    phone: "(03) 9416 2238",
    website: "nakedforsatan.com.au",
    tapBeers: ["Little Creatures Bright", "Hawkers Lager", "Prancing Pony", "Asahi"],
    specials: [
      {
        id: "s9",
        title: "Pintxos $2",
        description: "All pintxos $2 until 9pm daily",
        validUntil: "Daily until 9pm",
      },
    ],
    events: [],
    features: ["Rooftop", "Pintxos", "City Views", "Bar"],
    description:
      "The original rooftop bar. Three levels, legendary pintxos, and unbeatable Brunswick St vibes.",
    imageColor: "#c25400",
    latitude: -37.7945,
    longitude: 144.9779,
    openingHours: {
      Mon: "3:00 PM – 1:00 AM",
      Tue: "3:00 PM – 1:00 AM",
      Wed: "3:00 PM – 1:00 AM",
      Thu: "3:00 PM – 1:00 AM",
      Fri: "12:00 PM – 1:00 AM",
      Sat: "12:00 PM – 1:00 AM",
      Sun: "12:00 PM – 11:00 PM",
    },
    happyHour: {
      days: "Daily",
      times: "3:00 PM – 5:00 PM",
      deal: "$8 house beer & wine, all pintxos $2",
    },
    menuItems: [
      {
        category: "Pintxos (all $2)",
        items: [
          { name: "Jamon & Manchego", price: "$2" },
          { name: "Prawn & Aioli", price: "$2" },
          { name: "Mushroom & Truffle", price: "$2" },
          { name: "Chorizo & Romesco", price: "$2" },
          { name: "Brie & Fig", price: "$2" },
          { name: "Anchovy & Olive", price: "$2" },
        ],
      },
      {
        category: "Larger Plates",
        items: [
          { name: "Paella (for 2)", price: "$38", description: "Seafood, saffron, socarrat" },
          { name: "Cheese Board", price: "$22", description: "3 Spanish cheeses, membrillo, crackers" },
        ],
      },
    ],
  },
  {
    id: "9",
    name: "The Bowler Bar",
    suburb: "Collingwood",
    address: "96 Smith St, Collingwood",
    type: "pub",
    isOpen: true,
    closingTime: "1:00 AM",
    rating: 4.4,
    reviewCount: 198,
    phone: "(03) 9416 3450",
    website: "thebowlerbar.com.au",
    tapBeers: ["Hawkers Lager", "Moon Dog Fizzer", "Furphy", "4 Pines IPA"],
    specials: [
      {
        id: "s10",
        title: "Steak Night",
        description: "$28 eye fillet + chips + house beer, Tuesdays",
        validUntil: "Tuesdays",
      },
    ],
    events: [
      {
        id: "e7",
        title: "Trivia Night",
        date: "Tonight",
        time: "8:00 PM",
        description: "General knowledge. $3 entry per person.",
      },
    ],
    features: ["Beer Garden", "Pool Table", "Sports Screens", "Late Night"],
    description:
      "A no-fuss Collingwood local with a good kitchen and an even better beer garden.",
    imageColor: "#4a3520",
    latitude: -37.8024,
    longitude: 144.9862,
    mealDeal: "Steak Night",
    openingHours: {
      Mon: "12:00 PM – 11:00 PM",
      Tue: "12:00 PM – 12:00 AM",
      Wed: "12:00 PM – 12:00 AM",
      Thu: "12:00 PM – 1:00 AM",
      Fri: "12:00 PM – 1:00 AM",
      Sat: "11:00 AM – 1:00 AM",
      Sun: "11:00 AM – 10:00 PM",
    },
    happyHour: {
      days: "Daily",
      times: "4:00 PM – 6:00 PM",
      deal: "$6 schooners, $7 house wine & spirits",
    },
    menuItems: [
      {
        category: "Steaks",
        items: [
          { name: "Eye Fillet 200g", price: "$28", description: "Chips, salad & house beer (Tuesdays)" },
          { name: "Sirloin 300g", price: "$32", description: "Chips, mushroom sauce" },
          { name: "Rump 250g", price: "$26", description: "Chips, pepper sauce" },
        ],
      },
      {
        category: "Pub Favourites",
        items: [
          { name: "Chicken Parma", price: "$20", description: "Classic with chips & salad" },
          { name: "Beer-Battered Fish & Chips", price: "$18", description: "Flathead, tartare, lemon" },
          { name: "Vegetarian Lasagne", price: "$17", description: "Roasted veg, béchamel, garlic bread" },
        ],
      },
    ],
  },
  {
    id: "10",
    name: "The Penny Black",
    suburb: "Brunswick",
    address: "410 Sydney Rd, Brunswick",
    type: "pub",
    isOpen: true,
    closingTime: "12:00 AM",
    rating: 4.2,
    reviewCount: 145,
    phone: "(03) 9380 8111",
    website: "pennyblackbrunswick.com.au",
    tapBeers: ["Balter XPA", "Young Henrys Natural", "Carlton Draught", "Asahi"],
    specials: [
      {
        id: "s11",
        title: "Taco Tuesday",
        description: "$5 tacos + house beer from 5pm",
        validUntil: "Tuesdays from 5pm",
      },
    ],
    events: [
      {
        id: "e8",
        title: "Live Music: Local Bands",
        date: "Tonight",
        time: "8:30 PM",
        description: "Two local acts. Free entry all night.",
      },
    ],
    features: ["Live Music", "Beer Garden", "Dog Friendly", "Vegan Options"],
    description: "Brunswick's chill local. Great taco deals and solid live music roster.",
    imageColor: "#1e3a5f",
    latitude: -37.7591,
    longitude: 144.9612,
    mealDeal: "Taco Night",
    openingHours: {
      Mon: "4:00 PM – 12:00 AM",
      Tue: "4:00 PM – 12:00 AM",
      Wed: "4:00 PM – 12:00 AM",
      Thu: "4:00 PM – 12:00 AM",
      Fri: "12:00 PM – 12:00 AM",
      Sat: "12:00 PM – 12:00 AM",
      Sun: "12:00 PM – 10:00 PM",
    },
    happyHour: {
      days: "Mon – Fri",
      times: "4:00 PM – 6:00 PM",
      deal: "$6 schooners, $8 house cocktails",
    },
    menuItems: [
      {
        category: "Tacos (all $5 on Tuesdays)",
        items: [
          { name: "Pulled Pork Taco", price: "$7", description: "Chipotle, apple slaw, pickled jalapeño" },
          { name: "Fish Taco", price: "$7", description: "Beer-battered, chipotle mayo, cabbage" },
          { name: "Vegan Black Bean Taco (V)", price: "$6", description: "Salsa verde, avocado, coriander" },
        ],
      },
      {
        category: "Mains",
        items: [
          { name: "Smash Burger", price: "$18", description: "Double smash patty, pickles, American cheese" },
          { name: "Nachos", price: "$14", description: "Beans, cheese, jalapeños, guac, sour cream" },
        ],
      },
    ],
  },
];

export const CATEGORIES = [
  { id: "trivia", label: "Trivia Night", icon: "help-circle" },
  { id: "parma", label: "Parma Night", icon: "star" },
  { id: "live_music", label: "Live Music", icon: "music" },
  { id: "beer_garden", label: "Beer Garden", icon: "sun" },
  { id: "rooftop", label: "Rooftop", icon: "layers" },
  { id: "happy_hour", label: "Happy Hour", icon: "clock" },
  { id: "sports", label: "Sports", icon: "tv" },
  { id: "craft_beer", label: "Craft Beer", icon: "droplet" },
];

export const DRINK_TYPES = [
  "Craft Beer",
  "Lager",
  "IPA",
  "Pale Ale",
  "Cocktails",
  "Wine",
  "Cider",
];

export const VENUE_FEATURES = [
  "Beer Garden",
  "Rooftop",
  "Live Music",
  "Dog Friendly",
  "Sports Screens",
  "Pool Table",
  "Late Night",
  "Vegan Options",
];

export const DISTANCE_OPTIONS = [5, 10, 20, 50];
