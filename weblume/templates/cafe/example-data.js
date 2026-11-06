// All photos and frames are free stock, none show the real cafe yet. assets/img: Pexels 18286277, 10147669, 6615806, 8545199, 15353691, 6612700, 40262827, 17236225, 12975714, 11009226, 6747870, 18142624, 33526960, 4913342, 8004561; menu-drip: Mixkit 816
// Menu, prices and calories: the cafe's HungerStation page (restaurant 198511), linked from its Google Maps listing. In-store prices may differ.
// assets/brew-* : Pexels videos 30690821, 7487683, 6769788 and Mixkit 41859. assets/pour.mp4: Mixkit 796
window.CAFE = {
  name: "قهوة لوباي",
  word: "لوباي",
  nameEn: "LOOPIE CAFE",
  tagline: "نختلف عالجو.. ونتفق عالقهوة",
  lede: "قهوة مختصة وحلى نحضّره عندنا، على طريق الخليج في سيهات.",
  rating: { value: "4.8", count: 171 },
  hours: "24h",
  whatsapp: "966590595914",
  phone: "+966549663063",
  phoneText: "054 966 3063",
  instagram: "loopiecafe",
  tiktok: "loopiecafe",
  mapsQuery: "Loopiecafe, Khaleej Rd, Al Muntazah, Saihat",
  address: "طريق الخليج، حي المنتزه، سيهات 32452",
  about: "نجمع هنا أصحاب الذائقة الرفيعة من عشاق القهوة: محاصيل مختارة تتحضّر V60، وحلى نحضّره عندنا بنكهات مبتكرة.",
  aboutPhoto: { src: "assets/img/mood-yellow.webp", alt: "جلسة كوشن أصفر مع طاولة مستديرة" },
  hashtag: "#لوباي_يجمعنا",
  invite: "نورنا بقهوتك.",

  /* the live thing: each mood leads to a drink. img is a transparent cut-out, ratio its width/height, s its size */
  drinks: [
    { mood: "مستعجل", name: "إسبريسو", desc: "جرعة مركزة من محاصيل مختارة", img: "assets/img/drink-esp.webp", ratio: "800/550", s: .62, bg: "#FFFFFF", disc: "#EBB81F", fg: "#141210" },
    { mood: "الجو حر", name: "مقطرة باردة", desc: "قهوة مقطرة يدويًا مع الثلج", img: "assets/img/drink-amer.webp", ratio: "622/1011", s: 1, bg: "#141210", disc: "#D2A06A", fg: "#FFFFFF" },
    { mood: "جو هادي", name: "لاتيه", desc: "إسبريسو ناعم وحليب مبخّر", img: "assets/img/drink-capp.webp", ratio: "1070/1000", s: .72, bg: "#B5502F", disc: "#141210", fg: "#FFFFFF" },
    { mood: "جو شغل", name: "سبانيش لاتيه", desc: "إسبريسو وحليب وحليب مكثف محلى", img: "assets/img/drink-tall.webp", ratio: "440/1120", s: 1.12, bg: "#EBB81F", disc: "#FFFFFF", fg: "#141210" },
    { mood: "جو مختلف", name: "ليمون ماتشا", desc: "ماتشا منعشة وعصير ليمون طبيعي", img: "assets/img/drink-green.webp", ratio: "630/1060", s: 1, bg: "#2F4420", disc: "#557A35", fg: "#FFFFFF" }
  ],

  menuNote: "الأسعار والسعرات من صفحة الكافيه على هنقرستيشن، وممكن تختلف في المحل",
  order: "https://hungerstation.com/sa-ar/restaurant/sayhat/al-muntazah/198511",
  menu: [
    { name: "القهوة الباردة", img: "assets/img/drink-tall.webp", fit: "contain", alt: "لاتيه بارد في كوب طويل", items: [
      { name: "إسبريسو فريدو", desc: "جرعة اسبريسو مخفوقة وتقدم باردة ومنعشة مع مكعبات الثلج", price: 18.59, cal: 10 }
    ]},
    { name: "مشروبات بدون كافيين", img: "assets/img/drink-green.webp", fit: "contain", alt: "مشروب بارد منعش في كوب", items: [
      { name: "كركديه عنب", desc: "منقوع زهور الكركديه البارد بنكهة العنب الطبيعية مع قطع الثلج المنعشة", price: 30.42, cal: 120 },
      { name: "كركديه رمان", desc: "مشروب الكركديه المنعش مضاف إليه عصير الرمان الطبيعي ومكعبات الثلج", price: 28.73, cal: 130 },
      { name: "موهيتو توت أزرق", desc: "مشروب غازي منعش مع نكهة التوت الأزرق وأوراق النعناع وقطع الليمون", price: 32.11, cal: 160 },
      { name: "موهيتو توتيات", desc: "مزيج منعش من نكهات التوت المشكل مع المياه الغازية والليمون والنعناع", price: 32.11, cal: 170 },
      { name: "باشن فروت موهيتو", desc: "موهيتو منعش بنكهة فاكهة الباشن فروت الطبيعية مع النعناع والثلج المجروش", price: 32.11, cal: 150 }
    ]},
    { name: "المشروبات", img: "assets/img/menu-coffee.webp", alt: "لاتيه برسمة على الوجه", items: [
      { name: "إسبريسو برازيلي", desc: "جرعة اسبريسو مركزة مستخلصة من محصول حبوب البن البرازيلي", price: 16.9, cal: 5 },
      { name: "إسبريسو اثيوبي", desc: "قهوة اسبريسو مركزة محضرة من حبوب البن الاثيوبي الفاخر", price: 22.1, cal: 5 },
      { name: "إسبريسو يمني", desc: "جرعة قهوة اسبريسو مستخلصة من محصول البن اليمني المختص", price: 24.7, cal: 5 },
      { name: "إسبريسو باونتي", desc: "جرعة اسبريسو مركزة محضرة من سلالة حبوب باونتي المختصة", price: 22.1, cal: 5 },
      { name: "وايت موكا", desc: "مشروب قهوة اسبريسو ممزوج بالحليب المبخر وصوص الشوكولاتة البيضاء", price: 33.8, cal: 260 },
      { name: "دارك موكا", desc: "قهوة اسبريسو مخلوطة بالحليب الساخن وصوص الشوكولاتة الداكنة الغنية", price: 33.8, cal: 240 },
      { name: "لونق بلاك", desc: "قهوة سوداء كلاسيكية محضرة بإضافة الاسبريسو المركز فوق الماء الساخن", price: 18.59, cal: 10 },
      { name: "أمريكانو", desc: "جرعة اسبريسو غنية ومخففة بالماء الساخن للحصول على نكهة معتدلة", price: 20.28, cal: 15 },
      { name: "كورتادو", desc: "قهوة اسبريسو متوازنة مدمجة بكمية متساوية من الحليب الدافئ المبخر", price: 21.97, cal: 70 },
      { name: "فلات وايت", desc: "جرعة دبل اسبريسو ممزوجة بطبقة ناعمة من الحليب المبخر", price: 27.04, cal: 130 },
      { name: "كابتشينو", desc: "مزيج من الاسبريسو والحليب الدافئ مع طبقة رغوة كثيفة", price: 27.04, cal: 120 },
      { name: "لاتيه", desc: "قهوة اسبريسو ناعمة ممزوجة بكمية وافرة من الحليب الساخن المبخر", price: 30.42, cal: 150 },
      { name: "سبانيش لاتيه", desc: "قهوة اسبريسو مدمجة مع الحليب والحليب المكثف المحلى اللذيذ", price: 28.73, cal: 220 }
    ]},
    { name: "القهوة المقطرة", img: "assets/img/menu-drip.webp", alt: "ماء ساخن يصب على قهوة في فلتر", items: [
      { name: "قهوة مقطرة باردة شلشلي", desc: "قهوة مقطرة يدويا باردة بأداة الترشيح من محصول شلشلي", price: 31.2, cal: 5 },
      { name: "قهوة مقطرة باردة يمني", desc: "قهوة مثلجة مجهزة بالترشيح اليدوي من حبوب البن اليمني", price: 37.7, cal: 5 },
      { name: "قهوة مقطرة باردة كولومبي", desc: "قهوة مقطرة باردة محضرة من حبوب البن الكولومبي مع الثلج", price: 29.9, cal: 5 },
      { name: "قهوة مقطرة باردة باونتي", desc: "قهوة باردة مجهزة بالترشيح اليدوي ومستخلصة من حبوب بن باونتي", price: 37.7, cal: 5 },
      { name: "قهوة مقطرة باردة كوستاريكا", desc: "قهوة مقطرة باردة ومنعشة محضرة من محصول حبوب بن كوستاريكا", price: 29.9, cal: 5 },
      { name: "قهوة مقطرة ساخنة شلشلي", desc: "قهوة سوداء ساخنة محضرة بالتقطير اليدوي من محصول بن شلشلي", price: 31.2, cal: 5 },
      { name: "قهوة مقطرة ساخنة يمني", desc: "قهوة ساخنة مقطرة يدويا ومستخلصة من حبوب البن اليمني الفاخر", price: 37.7, cal: 5 },
      { name: "قهوة مقطرة ساخنة كولومبي", desc: "قهوة سوداء ساخنة بالترشيح اليدوي من محصول البن الكولومبي المختص", price: 29.9, cal: 5 },
      { name: "قهوة مقطرة ساخنة باونتي", desc: "قهوة مقطرة ساخنة مستخلصة بأداة الترشيح من حبوب بن باونتي", price: 37.7, cal: 5 },
      { name: "قهوة مقطرة ساخنة كوستاريكا", desc: "قهوة سوداء مقطرة بالماء الساخن ومحضرة من محصول بن كوستاريكا", price: 29.9, cal: 5 },
      { name: "بوكس قهوة اليوم 2 لتر", desc: "بوكس قهوة سوداء مجهزة بالترشيح اليومي تكفي لمشاركة العائلة والجمعات", price: 116.61, cal: 80 }
    ]},
    { name: "الماتشا", img: "assets/img/menu-matcha.webp", alt: "ماتشا بارد مع مضرب الخيزران", items: [
      { name: "كلاودي ماتشا", desc: "مشروب شاي الماتشا الياباني المخفوق مع الكريمة السحابية الناعمة والحليب", price: 43.94, cal: 210 },
      { name: "ليمون ماتشا", desc: "شاي الماتشا الأخضر المنعش ممزوج بعصير الليمون الطبيعي ومكعبات الثلج", price: 43.94, cal: 140 },
      { name: "مانجو ماتشا", desc: "مسحوق شاي الماتشا ممزوج مع بيوريه المانجو الطبيعي والحليب البارد", price: 47.32, cal: 230 },
      { name: "ماتشا الميلاد", desc: "مشروب ماتشا بنكهة احتفالية غنية مضاف إليها نكهات مميزة ومكعبات ثلج", price: 50.7, cal: 280 },
      { name: "باشن فروت ماتشا", desc: "شاي ماتشا منعش مخلوط مع نكهة فاكهة الباشن فروت الاستوائية والثلج", price: 47.32, cal: 180 },
      { name: "كريم بروليه ماتشا", desc: "شاي الماتشا الغني مضاف إليه طبقة كريم بروليه ناعمة ومكرملة", price: 43.94, cal: 290 }
    ]},
    { name: "الحلويات", img: "assets/img/menu-dessert.webp", alt: "قطع براونيز", items: [
      { name: "شوكلت كيك", desc: "كيكة غنية بطبقات الشوكولاتة الفاخرة ومحشوة بكريمة الكاكاو اللذيذة", price: 42.25, cal: 380 },
      { name: "براونيز", desc: "قطعة كعك براونيز غنية بقطع الشوكولاتة الذائبة ومخبوزة بقوام طري", price: 23.66, cal: 320 },
      { name: "كوكيز", desc: "بسكويت كوكيز مقرمش ولذيذ محضر بحبيبات الشوكولاتة البلجيكية", price: 21.97, cal: 240 },
      { name: "مانجو تشيز كيك", desc: "تشيز كيك كلاسيكي بطبقة جبنة غنية مغطى بصوص المانجو الطبيعي", price: 32.11, cal: 350 },
      { name: "تشيز كيك توت أحمر", desc: "تشيز كيك مخملي بقاعدة بسكويت هشة ومغطى بطبقة التوت الأحمر الطبيعي", price: 32.11, cal: 340 },
      { name: "تشيز كيك توت أزرق", desc: "كعكة جبنة كريمية غنية مغطاة بطبقة من صوص التوت الأزرق اللذيذ", price: 32.11, cal: 340 },
      { name: "لوتس تشيز كيك", desc: "تشيز كيك ناعم محضر بكريمة وبسكويت اللوتس المقرمش ومغطى بزبدة اللوتس", price: 32.11, cal: 390 },
      { name: "باشن فروت تشيز كيك", desc: "تشيز كيك غني بالجبن الكريمي مغطى بصلصة فاكهة الباشن فروت الاستوائية", price: 32.11, cal: 330 }
    ]}
  ],

  place: [
    { src: "assets/img/mood-tile.webp", alt: "مقعد من السيراميك مع كوشن" },
    { src: "assets/img/mood-chair.webp", alt: "كرسي بيج في ركن أبيض هادي" },
    { src: "assets/img/mood-stools.webp", alt: "طاولة صغيرة وكرسيين أسود على حائط أبيض" },
    { src: "assets/img/mood-hall.webp", alt: "صالة قهوة واسعة بنوافذ كبيرة" }
  ],
  visitPhoto: { src: "assets/img/mood-cup.webp", alt: "فنجان قهوة على البار بإضاءة دافئة" },
  en: {
    word: "Loopie",
    name: "Loopie Cafe",
    tagline: "We differ on the weather.. and agree on coffee",
    lede: "Specialty coffee and desserts made in-house, on Khaleej Road in Saihat.",
    address: "Khaleej Rd, Al Muntazah, Saihat 32452",
    about: "We bring together people of refined taste who love coffee: selected beans brewed as V60, and inventive desserts made in-house.",
    aboutPhoto: { alt: "Yellow cushioned seating with a round table" },
    hashtag: "#لوباي_يجمعنا",
    invite: "Have your coffee with us.",
    drinks: [
      { mood: "In a hurry", name: "Espresso", desc: "A concentrated shot from selected beans" },
      { mood: "It's hot out", name: "Iced Filter", desc: "Hand-brewed filter coffee over ice" },
      { mood: "Quiet", name: "Latte", desc: "Smooth espresso and steamed milk" },
      { mood: "Working", name: "Spanish Latte", desc: "Espresso, milk and sweetened condensed milk" },
      { mood: "Something new", name: "Lemon Matcha", desc: "Refreshing matcha with natural lemon juice" }
    ],
    menuNote: "Prices and calories from the cafe's HungerStation page, and may differ in store",
    menu: [
      { name: "Cold coffee", alt: "Iced latte in a tall glass", items: [
        { name: "Espresso Freddo", desc: "A shaken espresso shot, served cold over ice" }
      ]},
      { name: "Caffeine-free", alt: "A refreshing cold drink in a glass", items: [
        { name: "Grape Hibiscus", desc: "Cold hibiscus infusion with natural grape flavour and ice" },
        { name: "Pomegranate Hibiscus", desc: "Refreshing hibiscus with natural pomegranate juice and ice" },
        { name: "Blueberry Mojito", desc: "Sparkling drink with blueberry, mint leaves and lemon" },
        { name: "Mixed Berry Mojito", desc: "Mixed berries with sparkling water, lemon and mint" },
        { name: "Passion Fruit Mojito", desc: "Natural passion fruit with mint and crushed ice" }
      ]},
      { name: "Espresso drinks", alt: "Latte with art on top", items: [
        { name: "Brazilian Espresso", desc: "A concentrated shot from Brazilian beans" },
        { name: "Ethiopian Espresso", desc: "A concentrated shot from fine Ethiopian beans" },
        { name: "Yemeni Espresso", desc: "A shot from specialty Yemeni beans" },
        { name: "Bounty Espresso", desc: "A concentrated shot from the specialty Bounty variety" },
        { name: "White Mocha", desc: "Espresso with steamed milk and white chocolate sauce" },
        { name: "Dark Mocha", desc: "Espresso with hot milk and rich dark chocolate sauce" },
        { name: "Long Black", desc: "Classic black coffee: espresso poured over hot water" },
        { name: "Americano", desc: "Rich espresso lengthened with hot water for a mellow taste" },
        { name: "Cortado", desc: "Espresso balanced with an equal amount of warm steamed milk" },
        { name: "Flat White", desc: "A double espresso with a fine layer of steamed milk" },
        { name: "Cappuccino", desc: "Espresso and warm milk under a thick layer of foam" },
        { name: "Latte", desc: "Smooth espresso with plenty of hot steamed milk" },
        { name: "Spanish Latte", desc: "Espresso with milk and sweetened condensed milk" }
      ]},
      { name: "Filter coffee", alt: "Hot water poured over coffee in a filter", items: [
        { name: "Iced Filter, Chelchele", desc: "Cold hand-brewed filter coffee from Chelchele beans" },
        { name: "Iced Filter, Yemeni", desc: "Iced hand-brewed filter coffee from Yemeni beans" },
        { name: "Iced Filter, Colombian", desc: "Cold filter coffee from Colombian beans, over ice" },
        { name: "Iced Filter, Bounty", desc: "Cold hand-brewed filter coffee from Bounty beans" },
        { name: "Iced Filter, Costa Rica", desc: "Cold, refreshing filter coffee from Costa Rican beans" },
        { name: "Hot Filter, Chelchele", desc: "Hot black coffee, hand-dripped from Chelchele beans" },
        { name: "Hot Filter, Yemeni", desc: "Hot hand-dripped coffee from fine Yemeni beans" },
        { name: "Hot Filter, Colombian", desc: "Hot hand-brewed black coffee from specialty Colombian beans" },
        { name: "Hot Filter, Bounty", desc: "Hot filter coffee from Bounty beans" },
        { name: "Hot Filter, Costa Rica", desc: "Black coffee dripped with hot water from Costa Rican beans" },
        { name: "Coffee of the Day Box, 2 L", desc: "Black filter coffee brewed daily, made for sharing" }
      ]},
      { name: "Matcha", alt: "Iced matcha with a bamboo whisk", items: [
        { name: "Cloudy Matcha", desc: "Whisked Japanese matcha with soft cloud cream and milk" },
        { name: "Lemon Matcha", desc: "Refreshing matcha with natural lemon juice and ice" },
        { name: "Mango Matcha", desc: "Matcha with natural mango purée and cold milk" },
        { name: "Birthday Matcha", desc: "A rich, festive matcha with special flavours and ice" },
        { name: "Passion Fruit Matcha", desc: "Refreshing matcha with tropical passion fruit and ice" },
        { name: "Crème Brûlée Matcha", desc: "Rich matcha under a smooth, caramelized crème brûlée layer" }
      ]},
      { name: "Desserts", alt: "Brownie pieces", items: [
        { name: "Chocolate Cake", desc: "Rich layers of fine chocolate, filled with cocoa cream" },
        { name: "Brownies", desc: "Soft-baked brownie, rich with melted chocolate" },
        { name: "Cookies", desc: "Crisp cookies with Belgian chocolate chips" },
        { name: "Mango Cheesecake", desc: "Classic cheesecake topped with natural mango sauce" },
        { name: "Red Berry Cheesecake", desc: "Velvety cheesecake on a crisp base, topped with red berries" },
        { name: "Blueberry Cheesecake", desc: "Rich, creamy cheesecake with blueberry sauce" },
        { name: "Lotus Cheesecake", desc: "Smooth cheesecake with Lotus biscuit and Lotus spread" },
        { name: "Passion Fruit Cheesecake", desc: "Rich cream cheese topped with tropical passion fruit sauce" }
      ]}
    ],
    place: [
      { alt: "Tiled bench with cushions" },
      { alt: "Beige armchair in a quiet white corner" },
      { alt: "Small table and two black stools by a white wall" },
      { alt: "A wide coffee room with large windows" }
    ],
    visitPhoto: { alt: "A cup of coffee on the bar in warm light" }
  },
  demo: true
};
