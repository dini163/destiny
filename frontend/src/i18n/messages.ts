/**
 * Locale dictionaries keyed by the source Simplified-Chinese string.
 *
 * Design: source Chinese acts as the lookup key, so wrapping an existing
 * string with `t('原文')` requires no key naming and never drifts from a
 * renamed ID. `zh-Hans` is intentionally absent — its identity IS the source;
 * `t()` returns the key unchanged when the locale has no entry, which also
 * lets tests render without a Provider and still see source text.
 *
 * Phase 1 covers app chrome (header, footer, brand, controls) plus the entry
 * experience (portal hero, questions, system cards, catalogue), the router
 * Suspense fallback, and the 404 / route-error surfaces. Per-system result
 * pages, forms (InputBar, LocationField, ProfileEditor) and the backend
 * judgment corpora (`app/engines/plain_corpora` — 4,000+ zh-Hans entries)
 * are phase 2; when their text is wrapped with `t()` they will surface
 * untranslated until added below.
 */
import type { AppLocale } from '../lib/locale';

export type MessageDict = Readonly<Record<string, string>>;

const zhHant: MessageDict = {
  // SiteHeader + brand
  'Destiny 测算大厅': 'Destiny 測算大廳',
  主导航: '主導覽',
  发现: '發現',
  从问题开始: '從問題開始',
  报告样例: '報告样例',
  探索全部体系: '探索全部體系',
  我的档案: '我的檔案',
  打开体系导航: '開啟體系導覽',
  关闭体系导航: '關閉體系導覽',
  '以你熟悉的方式，开始探索。': '以你熟悉的方式，開始探索。',
  全体系导航: '全體系導覽',
  快捷入口: '快捷入口',
  '观己 · 知时 · 懂相处': '觀己 · 知時 · 懂相處',

  // Primary nav
  测算大厅: '測算大廳',
  八字排盘: '八字排盤',
  西洋占星: '西洋占星',
  塔罗神谕: '塔羅神諭',
  周易六爻: '周易六爻',

  // Secondary nav groups
  华夏术数: '華夏術數',
  西洋秘学: '西洋秘學',
  吠陀与北欧: '吠陀與北歐',

  // Secondary nav items
  八字命理: '八字命理',
  岁运推演: '歲運推演',
  紫微斗数: '紫微斗數',
  奇门遁甲: '奇門遁甲',
  文王六爻: '文王六爻',
  梅花易数: '梅花易數',
  八字合婚: '八字合婚',
  五格姓名学: '五格姓名學',
  本命星盘: '本命星盤',
  行运推运: '行運推運',
  双人合盘: '雙人合盤',
  经典塔罗: '經典塔羅',
  雷诺曼: '雷諾曼',
  卡巴拉: '卡巴拉',
  毕氏灵数: '畢氏靈數',
  吠陀乔蒂什: '吠陀喬蒂什',
  北欧卢恩: '北歐盧恩',

  // SiteFooter
  合规免责声明: '合規免責聲明',
  '本平台所有命理排盘、星历计算及推演结果均基于数理模型与民俗哲学古籍整理，结果仅供娱乐与文化参考，不构成任何医疗、法律、财务或重大人生命运决策建议。':
    '本平台所有命理排盤、星曆計算及推演結果均基於數理模型與民俗哲學古籍整理，結果僅供娛樂與文化參考，不構成任何醫療、法律、財務或重大人生命運決策建議。',
  了解排盘依据与隐私保存: '了解排盤依據與隱私保存',
  天文与时空基准: '天文與時空基準',
  '以权威星历推算行星黄经与宫头；真太阳时按经度时差（每度 4 分钟）与均时差动态校准，经纬度解析全球坐标。':
    '以權威星曆推算行星黃經與宮頭；真太陽時按經度時差（每度 4 分鐘）與均時差動態校準，經緯度解析全球座標。',
  古籍历法溯源: '古籍曆法溯源',
  '依权威历法严谨推算二十四节气换气定柱；卦爻辞锚定《周易》通行本原文，杜绝虚构易辞与生搬硬造的星盘断语。':
    '依權威曆法嚴謹推算二十四節氣換氣定柱；卦爻辭錨定《周易》通行本原文，杜絕虛構易辭與生搬硬造的星盤斷語。',
  隐私与天机安全: '隱私與天機安全',
  '普通排盘不在服务端保存。我的档案、卢恩秘匣和主题偏好保存在本机浏览器；报告输入在当前标签页暂存。人工确认交付的报告会在服务端保存固定版本直至到期清理。下钻链接可能包含生辰和地点，请勿公开转发；浏览器历史、下载文件和服务访问日志需分别管理。':
    '普通排盤不在服務端儲存。我的檔案、盧恩秘匣和主題偏好儲存於本機瀏覽器；報告輸入在目前分頁暫存。人工確認交付的報告會在服務端儲存固定版本直至到期清理。下鑽連結可能包含生辰和地點，請勿公開轉發；瀏覽器歷史、下載檔案和服務存取日誌需分別管理。',

  // LocalDataControls
  管理本机档案与收藏: '管理本機檔案與收藏',
  '档案、卢恩收藏只存本机，没有自动加密或云端备份。清除会删除这些记录及当前报告输入，不会删除下载文件或浏览器历史。':
    '檔案、盧恩收藏只存本機，沒有自動加密或雲端備份。清除會刪除這些記錄及目前報告輸入，不會刪除下載檔案或瀏覽器歷史。',
  导出本机记录: '匯出本機記錄',
  清除本机记录: '清除本機記錄',
  '请先导出需要保留的记录。确认清除所有本机档案和卢恩收藏？':
    '請先匯出需要保留的記錄。確認清除所有本機檔案和盧恩收藏？',
  确认清除: '確認清除',
  取消: '取消',
  '导出文件可能含姓名、生辰与问题记录，请妥善保管。':
    '匯出檔案可能含姓名、生辰與問題記錄，請妥善保管。',
  '无法导出，请检查浏览器的存储权限。': '無法匯出，請檢查瀏覽器的儲存權限。',
  '清除未能完成，请使用浏览器的网站数据设置。':
    '清除未能完成，請使用瀏覽器的網站資料設定。',

  // ThemeToggle
  切换为曜石深色: '切換為曜石深色',
  切换为暖纸白: '切換為暖紙白',

  // PortalHero
  '把古老的智慧，': '把古老的智慧，',
  '读成自己的答案。': '讀成自己的答案。',
  '从了解自己，到读懂一段关系。': '從了解自己，到讀懂一段關係。',
  '把复杂的排盘，整理成你看得懂、用得上的生活观察。':
    '把複雜的排盤，整理成你看得懂、用得上的生活觀察。',
  从你关心的问题开始: '從你關心的問題開始',
  先读一份真实样例: '先讀一份真實样例',
  有据可查的排盘: '有據可查的排盤',
  读得懂的解读: '讀得懂的解讀',
  留给自己的选择: '留給自己的選擇',
  '天体轨道装饰，不代表实际星体位置': '天體軌道裝飾，不代表實際星體位置',
  每一份排盘: '每一份排盤',
  都是一次重新认识自己的起点: '都是一次重新認識自己的起點',
  开始八字排盘: '開始八字排盤',

  // PortalPage
  全部体系: '全部體系',
  '先读结论，再看它从何而来。': '先讀結論，再看它從何而來。',
  '排盘依据、传统解释与生活建议，分层阅读。你可以参考，也可以保留不同的看法。':
    '排盤依據、傳統解釋與生活建議，分層閱讀。你可以參考，也可以保留不同的看法。',
  '探索全部 {{count}} 个体系': '探索全部 {{count}} 個體系',
  '找到你熟悉的那一种视角。': '找到你熟悉的那一種視角。',
  体系类目筛选: '體系類目篩選',
  了解本次授时与历算基准: '了解本次授時與曆算基準',

  // QuestionEntries
  '此刻，你更想了解什么？': '此刻，你更想了解什麼？',
  '不必先懂术语，从一个真实的关心开始。':
    '不必先懂術語，從一個真實的關心開始。',
  '我怎样，才能更好地用自己？': '我怎樣，才能更好地用自己？',
  关于自己: '關於自己',
  '看见驱动力、压力反应与相处需求，找到适合自己的节奏。':
    '看見驅動力、壓力反應與相處需求，找到適合自己的節奏。',
  '我们为什么亲近，又为何摩擦？': '我們為什麼親近，又為何摩擦？',
  关于关系: '關於關係',
  '从双方的需求与差异出发，把抽象的互补读成可讨论的议题。':
    '從雙方的需求與差異出發，把抽象的互補讀成可討論的議題。',
  '下一阶段，我想怎样安排？': '下一階段，我想怎樣安排？',
  关于节奏: '關於節奏',
  '了解年度与流月的传统解读，再结合自己的现实计划做取舍。':
    '了解年度與流月的傳統解讀，再結合自己的現實計畫做取捨。',
  开始探索: '開始探索',

  // Portal system catalogue — nameZh
  '西洋本命星盘': '西洋本命星盤',
  '经典塔罗神谕': '經典塔羅神諭',
  '雷诺曼神谕': '雷諾曼神諭',
  '行运次限推运': '行運次限推運',
  '毕达哥拉斯灵数': '畢達哥拉斯靈數',
  '卡巴拉生命之树': '卡巴拉生命之樹',
  '合盘与相契度': '合盤與相契度',
  '北欧卢恩符文': '北歐盧恩符文',

  // Portal system catalogue — blurbs / highlights / ctas
  '《渊海子平》正宗四柱推演，以天干地支五行生克制化，厘定身强身弱与十神大运走势。':
    '《淵海子平》正宗四柱推演，以天干地支五行生克制化，釐定身強身弱與十神大運走勢。',
  十神精微: '十神精微',
  真太阳时: '真太陽時',
  立即排盘: '立即排盤',
  '文王六十四卦精研，京房纳甲卦变。铜钱三掷起卦，定世应六亲六神，附通行本卦爻辞原文。':
    '文王六十四卦精研，京房納甲卦變。銅錢三擲起卦，定世應六親六神，附通行本卦爻辭原文。',
  古籍原文: '古籍原文',
  世应动爻: '世應動爻',
  摇铜求卦: '搖銅求卦',
  '基于普拉西德分宫制与精密黄道，解构日月升、十行星落座落宫、相位与守护格局。':
    '基於普拉西德分宮制與精密黃道，解構日月升、十行星落座落宮、相位與守護格局。',
  瑞士星历: '瑞士星曆',
  精密相位: '精密相位',
  测绘星图: '測繪星圖',
  '78 张伟特系大小阿卡纳原生牌阵，凯尔特十字、时间之流与关系牌阵深度洞察。':
    '78 張偉特系大小阿卡納原生牌陣，凱爾特十字、時間之流與關係牌陣深度洞察。',
  洗牌抽卡: '洗牌抽卡',
  牌阵解析: '牌陣解析',
  开启抽牌: '開啟抽牌',
  '十二宫垣星曜罗列，紫微天府南北斗交辉，四化飞星直断流年大限气数。':
    '十二宮垣星曜羅列，紫微天府南北斗交輝，四化飛星直斷流年大限氣數。',
  十二宫四化体系: '十二宮四化體系',
  排定命盘: '排定命盤',
  '帝王之术，九星八门八神九宫定局，天地人神四盘交错，谋定决策时空场。':
    '帝王之術，九星八門八神九宮定局，天地人神四盤交錯，謀定決策時空場。',
  时家转盘法: '時家轉盤法',
  起局排盘: '起局排盤',
  '邵康节灵应法门，随感随应、物象心机，报数方位声色皆可起体用卦象。':
    '邵康節靈應法門，隨感隨應、物象心機，報數方位聲色皆可起體用卦象。',
  体用互变论: '體用互變論',
  起卦断体用: '起卦斷體用',
  '康熙字典原笔画核定，天格地格人格总格外格相生相克数理吉凶。':
    '康熙字典原筆畫核定，天格地格人格總格外格相生相克數理吉凶。',
  '81 数理吉凶表': '81 數理吉凶表',
  核定笔画: '核定筆畫',
  '欧式 36 张生活微观象征图画，大画卷（Grand Tableau）全景排布直析吉凶线索。':
    '歐式 36 張生活微觀象徵圖畫，大畫卷（Grand Tableau）全景排布直析吉凶線索。',
  '36 张全景大阵': '36 張全景大陣',
  洗牌抽牌: '洗牌抽牌',
  '外行星过境、太阳弧与次限法双重时间轴对碰，动态叠加本命盘。':
    '外行星過境、太陽弧與次限法雙重時間軸對碰，動態疊加本命盤。',
  多盘动态重叠: '多盤動態重疊',
  叠加行运盘: '疊加行運盤',
  '生命灵数、表达数与灵魂冲动数，以数字震动频率洞察天赋潜能与流年周期。':
    '生命靈數、表達數與靈魂衝動數，以數字震動頻率洞察天賦潛能與流年週期。',
  双九宫矩阵: '雙九宮矩陣',
  推演灵数: '推演靈數',
  '十原质（Sephiroth）与 22 条神圣路径，对应塔罗大阿卡纳与希伯来字母创世密源。':
    '十原質（Sephiroth）與 22 條神聖路徑，對應塔羅大阿卡納與希伯來字母創世密源。',
  原质路径升华: '原質路徑昇華',
  探索生命之树: '探索生命之樹',
  '双人本命比较盘（Synastry）人对人相位、短弧中点组合盘（Composite）与相契度总分账本，直击两人因缘契合力学。':
    '雙人本命比較盤（Synastry）人對人相位、短弧中點組合盤（Composite）與相契度總分賬本，直擊兩人因緣契合力學。',
  双轮合盘: '雙輪合盤',
  相契度账本: '相契度賬本',
  开始合盘: '開始合盤',
  '基于恒星黄道（Lahiri Ayanamsa）及 27 宿（Nakshatras），推演业力因果与达夏大运。':
    '基於恆星黃道（Lahiri Ayanamsa）及 27 宿（Nakshatras），推演業力因果與達夏大運。',
  '南印 / 北印方盘': '南印 / 北印方盤',
  排定星盘: '排定星盤',
  '24 枚古老弗萨克字符石，序位据 Kylver 石碑；单枚启示、诺伦三女神运命之阵与卢恩十字，另可启用现代增补的空白符。':
    '24 枚古老弗薩克字元石，序位據 Kylver 石碑；單枚啟示、諾倫三女神運命之陣與盧恩十字，另可啟用現代增補的空白符。',
  三种牌阵: '三種牌陣',
  全典检索: '全典檢索',
  掷符铸石: '擲符鑄石',

  // Router fallback / NotFound / RouteError
  '正在打开页面…': '正在開啟頁面…',
  迷失星域: '迷失星域',
  '未找到该路径对应的秘术体系，请返回测算大厅重新起盘。':
    '未找到該路徑對應的秘術體系，請返回測算大廳重新起盤。',
  返回测算大厅: '返回測算大廳',
  '页面刚刚更新，请重新载入。': '頁面剛剛更新，請重新載入。',
  '这个页面暂时无法打开。': '這個頁面暫時無法開啟。',
  '已保存的本机档案不会因此删除。你可以重试，或回到首页继续探索。':
    '已儲存的本機檔案不會因此刪除。你可以重試，或回到首頁繼續探索。',
  重新载入: '重新載入',
  回到首页: '回到首頁',

  // --- Phase 2.1 · shared UI chrome ---
  // InputBar internals
  公历: '公曆',
  农历: '農曆',
  历法: '曆法',
  '把当前生辰与出生地存入本地档案': '把當前生辰與出生地存入本機檔案',
  填写生辰后即可存入档案: '填寫生辰後即可存入檔案',
  存入档案: '存入檔案',
  '生辰（精准至分）': '生辰（精準至分）',
  '出生基准地（全球坐标）': '出生基準地（全球座標）',
  '填写出生日期、时间并完成经纬度定位后即可排盘。':
    '填寫出生日期、時間並完成經緯度定位後即可排盤。',
  '填写出生日期、时间并完成定位后即可排盘。':
    '填寫出生日期、時間並完成定位後即可排盤。',

  // LocationField
  '搜索城市，或下方直接填写经纬度': '搜尋城市，或於下方直接填寫經緯度',
  出生城市搜索: '出生城市搜尋',
  清除地点: '清除地點',
  '城市查询服务暂时不可用，请检查后端服务是否启动，或在下方手动填写经纬度。':
    '城市查詢服務暫時無法使用，請檢查後端服務是否啟動，或於下方手動填寫經緯度。',
  重试查询: '重試查詢',
  '未匹配到「{{term}}」，请在下方手动填写经纬度。':
    '未匹配到「{{term}}」，請於下方手動填寫經緯度。',
  纬度: '緯度',
  经度: '經度',
  手动坐标: '手動座標',

  // DateTimeField unit labels + aria default
  年: '年',
  月: '月',
  日: '日',
  时: '時',
  分: '分',
  出生: '出生',

  // TrueSolarTimeBadge
  '填写出生日期、时间并定位后，此处按经度与均时差显示真太阳时校准。':
    '填寫出生日期、時間並定位後，此處依經度與均時差顯示真太陽時校準。',
  真太阳时校准定盘: '真太陽時校準定盤',
  标准时: '標準時',
  '正在按经度与均时差推算…': '正在依經度與均時差推算…',
  '真太阳时服务暂不可用。': '真太陽時服務暫不可用。',
  '等待计算…': '等待計算…',
  校正: '校正',

  // VerdictCard
  综合结论: '綜合結論',
  星: '星',

  // ProfilePicker
  选择档案: '選擇檔案',
  男: '男',
  女: '女',
  未填生辰: '未填生辰',
  '不使用档案（清空）': '不使用檔案（清空）',
  管理档案: '管理檔案',
  '还没有档案。先去建一个，测算时就能一键填充。':
    '還沒有檔案。先建一個，測算時就能一鍵填充。',
  去创建档案: '去建立檔案',

  // ProfileEditor dialog
  编辑档案: '編輯檔案',
  新建档案: '新建檔案',
  关闭: '關閉',
  '仅保存在本机浏览器，不上传服务器，可随时编辑或删除。':
    '僅儲存在本機瀏覽器，不上傳伺服器，可隨時編輯或刪除。',
  '档案名（必填）': '檔案名（必填）',
  '如 我自己 / 父亲 / 长子': '如 我自己 / 父親 / 長子',
  给自己起个称呼: '給自己取個稱呼',
  档案名: '檔案名',
  '姓氏（供姓名学拆分）': '姓氏（供姓名學拆分）',
  '如 陸': '如 陸',
  姓氏: '姓氏',
  名字: '名字',
  '如 青玄': '如 青玄',
  性别: '性別',
  出生日期: '出生日期',
  出生时间: '出生時間',
  '出生地（全球坐标）': '出生地（全球座標）',
  保存修改: '儲存修改',

  // Page-level InputBar titles / badges / common chrome (shared across bazi-style pages)
  权威历算: '權威曆算',
  恒星黄道: '恆星黃道',
  排盘中: '排盤中',
  开始排盘: '開始排盤',
  '造向（性别）': '造向（性別）',
  '命主称谓（可选，仅回显）': '命主稱謂（選填，僅回顯）',
  '如：示例命主': '如：示例命主',
  '真太阳时校正（推荐）': '真太陽時校正（建議）',
  '正在依据真太阳时排定四柱…': '正在依據真太陽時排定四柱…',
  本命使用说明书: '本命使用說明書',
  四柱八字精算排盘: '四柱八字精算排盤',
  '真太阳时经度校正与节气精确交节，一次排定干支、十神、藏干、纳音、身强身弱与大运流年。示例：1988-02-15 23:30 · 成都 · 乾造（男）。':
    '真太陽時經度校正與節氣精確交節，一次排定干支、十神、藏干、納音、身強身弱與大運流年。示例：1988-02-15 23:30 · 成都 · 乾造（男）。',
  四柱命造干支矩阵: '四柱命造干支矩陣',
  四柱: '四柱',
  地支藏干权重与十神: '地支藏干權重與十神',
  '藏干十神': '藏干十神',
  五行能量量化分布: '五行能量量化分佈',
  五行: '五行',
  日主强弱与格局: '日主強弱與格局',
  强弱格局: '強弱格局',
  '用神三法（扶抑 / 通关 / 调候）': '用神三法（扶抑 / 通關 / 調候）',
  '用神三法': '用神三法',
  神煞命中: '神煞命中',
  神煞: '神煞',
  '刑冲合害破与合会局': '刑沖合害破與合會局',
  刑冲合害: '刑沖合害',
  大运流变时间轴: '大運流變時間軸',
  大运: '大運',
  六维详批: '六維詳批',
  命盘分区: '命盤分區',
  推演此造岁运流年: '推演此造歲運流年',
  以此造合婚: '以此造合婚',
  '当前大运 ·': '當前大運 ·',
  '此运与四柱之间未构成伏吟或反吟。': '此運與四柱之間未構成伏吟或反吟。',
  岁: '歲',
  四柱命造: '四柱命造',
  生肖: '生肖',
  日元: '日元',
  命宫: '命宮',
  胎元: '胎元',
  参照日: '參照日',

  // ReportEntryBar internals (parameterised; pages pass source `productName` verbatim)
  '本盘已排定，可进一步生成《{{productName}}》——按问题组织的深度解读报告。':
    '本盤已排定，可進一步生成《{{productName}}》——按問題組織的深度解讀報告。',
  生成报告: '生成報告',

  // BaziNatal · ChartSummary inline heading + colon labels + tst variants
  '四柱命造 · FOUR PILLARS': '四柱命造 · FOUR PILLARS',
  '农历：': '農曆：',
  '标准时：': '標準時：',
  '经度：': '經度：',
  '真太阳时 {{tst}}（校正 {{offset}} 分）': '真太陽時 {{tst}}（校正 {{offset}} 分）',
  '未校正（标准时直排）': '未校正（標準時直排）',

  // --- Phase 2.3 · Tarot / Lenormand / PlumBlossom / Zhouyi page chrome ---
  // Tarot
  '正在洗牌布阵…': '正在洗牌布陣…',
  已全部翻开: '已全部翻開',
  翻开全部: '翻開全部',
  '点选任意牌张即可翻开并展开详解；逆位牌以颠倒方向呈现。':
    '點選任意牌張即可翻開並展開詳解；逆位牌以顛倒方向呈現。',
  牌阵盘面: '牌陣盤面',
  牌义详解: '牌義詳解',
  围绕你选择的主题: '圍繞你選擇的主題',
  综合解读: '綜合解讀',

  // Lenormand
  '正在洗牌抽牌，铺陈牌阵…': '正在洗牌抽牌，鋪陳牌陣…',
  '第 {{n}} 位 ·': '第 {{n}} 位 ·',
  张: '張',
  所问之事: '所問之事',
  '点击牌阵中任意一张牌，查看其完整牌义。':
    '點擊牌陣中任意一張牌，檢視其完整牌義。',
  核心牌义: '核心牌義',
  '名词核心：': '名詞核心：',
  '；作后牌修饰前牌时：': '；作後牌修飾前牌時：',
  牌阵布局: '牌陣布局',
  组合直读透镜: '組合直讀透鏡',
  综合判读: '綜合判讀',

  // PlumBlossom
  '正在起卦，推演体用互变…': '正在起卦，推演體用互變…',
  '本卦 → 变卦 · PRIMARY TO CHANGED': '本卦 → 變卦 · PRIMARY TO CHANGED',
  '起卦推演 · DERIVATION': '起卦推演 · DERIVATION',
  所占之事: '所占之事',
  起卦时刻: '起卦時刻',
  月令卦气: '月令卦氣',
  当令: '當令',
  体卦: '體卦',
  用卦: '用卦',
  '互卦 · 事之中段': '互卦 · 事之中段',
  '变卦 · 事之归宿': '變卦 · 事之歸宿',
  卦象三盘: '卦象三盤',
  体用生克: '體用生剋',
  吉凶指数: '吉凶指數',
  互变推演: '互變推演',

  // Zhouyi
  '正在起卦排盘，推演纳甲六亲…': '正在起卦排盤，推演納甲六親…',
  整卦白话: '整卦白話',
  纳甲六亲盘: '納甲六親盤',
  起卦记录: '起卦記錄',
  变卦: '變卦',
  '本卦动爻阴阳互变得变卦，示事之趋向。':
    '本卦動爻陰陽互變得變卦，示事之趨向。',
  '六爻安静，本卦无动爻，故无变卦。占断以本卦卦辞与世应为主。':
    '六爻安靜，本卦無動爻，故無變卦。占斷以本卦卦辭與世應為主。',
  互卦: '互卦',
  '取本卦二三四爻为下卦、三四五爻为上卦，得互卦，示事之中段。':
    '取本卦二三四爻為下卦、三四五爻為上卦，得互卦，示事之中段。',
  卦爻辞: '卦爻辭',
  '六爻安静 · 无变卦': '六爻安靜 · 無變卦',
  '{{count}} 爻动': '{{count}} 爻動',
  日柱: '日柱',
  本卦宫: '本卦宮',
  动爻: '動爻',
  无: '無',
  动: '動',

  // --- Phase 2.4 · Qimen / Ziwei page chrome ---
  // Qimen
  '正在起局，布地盘、转九星八门八神…': '正在起局，布地盤、轉九星八門八神…',
  全局白话: '全局白話',
  洛书九宫盘: '洛書九宮盤',
  九宫白话: '九宮白話',
  '定局 · JU DETERMINATION': '定局 · JU DETERMINATION',
  值符: '值符',
  值使: '值使',
  落: '落',
  宫: '宮',
  年柱: '年柱',
  月柱: '月柱',
  时柱: '時柱',
  时辰旬首: '時辰旬首',
  '{{xs}}（遁{{yi}}）': '{{xs}}（遁{{yi}}）',
  旬空: '旬空',
  驿马: '驛馬',
  用事时刻: '用事時刻',
  占问事项: '占問事項',

  // Ziwei
  '正在安星排盘，布列十二宫垣…': '正在安星排盤，布列十二宮垣…',
  全盘白话: '全盘白話',
  十二宫命盘: '十二宮命盤',
  十二宫白话: '十二宮白話',
  '紫微斗数命盘 · ZI WEI DOU SHU': '紫微斗數命盤 · ZI WEI DOU SHU',
  造向: '造向',
  命主: '命主',
  身主: '身主',
  紫微: '紫微',
  天府: '天府',
  '（闰）': '（閏）',
  '身宫：': '身宮：',
  '大限：': '大限：',
  岁起运: '歲起運',
  '历法：': '曆法：',

  // NorseRunes
  '正在铸石…': '正在鑄石…',
  '{{count}} 枚石碑': '{{count}} 枚石碑',
  导出符印命谱: '導出符印命譜',

  // Report page
  '关系阶段（可选）': '關係階段（可選）',
  暂不提供: '暫不提供',
  相识或交往: '相識或交往',
  长期相处: '長期相處',
  修复分歧: '修復分歧',
  '只用于组织沟通建议，不改变盘面计算。':
    '僅用於組織溝通建議，不改變盤面計算。',
  报告起始日: '報告起始日',
  '不选则从今天开始，连续十二个月。': '不選則從今天起，連續十二個月。',
  返回发现: '返回發現',
  '真实计算样例 · 非个人测评': '真實計算樣例 · 非個人測評',
  私密报告交付: '私密報告交付',
  报告预览: '報告預覽',
  '正在准备报告…': '正在準備報告…',

  // Profiles page
  '把常用之人的生辰与出生地存成本地档案：八字、紫微、西洋占星等任一测算页点「选择档案」即可一键填充，测算后也可把当前输入一键存入。':
    '把常用之人的生辰與出生地存為本機檔案：八字、紫微、西洋占星等任一測算頁點「選擇檔案」即可一鍵填充，測算後亦可把當前輸入一鍵存入。',
  '档案只写在你这台设备的浏览器里，不上传服务器，不随账号漫游，可随时编辑或删除。':
    '檔案只寫在你這台裝置的瀏覽器裡，不上傳伺服器，不隨帳號漫遊，可隨時編輯或刪除。',
  '{{count}} 份档案 · 本机存储': '{{count}} 份檔案 · 本機儲存',
  还没有档案: '還沒有檔案',
  '点击「新建档案」录入第一位家人或朋友，之后在任何测算页都能从「选择档案」一键带入其生辰。':
    '點擊「新建檔案」錄入第一位家人或朋友，之後在任何測算頁都能從「選擇檔案」一鍵帶入其生辰。',
  新建第一份档案: '新建第一份檔案',
  未填性别: '未填性別',
  '更新于 {{date}}': '更新於 {{date}}',
  编辑: '編輯',
  确认删除: '確認刪除',
  删除: '刪除',

  // Kabbalah page
  '正在展开生命之树…': '正在展開生命之樹…',
  'TREE OF LIFE · {{sep}} 原质 · {{path}} 路径': 'TREE OF LIFE · {{sep}} 原質 · {{path}} 路徑',
  '点选原质或路径，展开象征对应': '點選原質或路徑，展開象徵對應',
  生命之树: '生命之樹',
  全树白话: '全樹白話',
  '原质 / 路径详解': '原質 / 路徑詳解',
  'gematria 数理折入': 'gematria 數理折入',
  '十原质 · SEPHIROTH': '十原質 · SEPHIROTH',
  '22 路径 · PATHS': '22 路徑 · PATHS',
  '生命之树是卡巴拉的核心图示：神圣之光自': '生命之樹是卡巴拉的核心圖示：神聖之光自',
  '王冠（Kether）': '王冠（Kether）',
  '逐级降落，经': '逐級降落，經',
  '十原质（Sephiroth）': '十原質（Sephiroth）',
  '显化为物质世界的': '顯化為物質世界的',
  '王国（Malkuth）': '王國（Malkuth）',
  '；十原质之间由 22 条路径相连，每条路径对应一个希伯来字母、一张塔罗大阿卡纳与一组行星／星座／元素。点选任意原质或路径，即可查其黄金黎明（Golden Dawn）体系下的完整对应。':
    '；十原質之間由 22 條路徑相連，每條路徑对应一個希伯來字母、一張塔羅大阿卡納與一組行星／星座／元素。點選任意原質或路徑，即可查其黄金黎明（Golden Dawn）體系下的完整對應。',

  // Name page
  选档案填姓名: '選檔案填姓名',
  '正在核定康熙笔画并推演五格…': '正在核定康熙筆畫並推演五格…',
  字级溯源: '字級溯源',
  五格: '五格',
  三才: '三才',
  综合指数: '綜合指數',
  康熙笔画核定: '康熙筆畫核定',
  五格剖象全景图谱: '五格剖象全景圖譜',
  三才配置深度研判: '三才配置深度研判',
  姓名综合气象指数: '姓名綜合氣象指數',
  姓名学分区: '姓名學分區',
  '核定姓名 · RESOLVED': '核定姓名 · RESOLVED',
  '以下字的康熙笔画不在本语料范围内，相关五格与指数不予推算：':
    '以下字的康熙筆畫不在本語料範圍內，相關五格與指數不予推算：',

  // Numerology page
  出错字段: '出错字段',
  '把姓名换成拼音或英文名后重新推演；中文名可填在选填格里，仅作回显、不参与计算。':
    '把姓名換成拼音或英文名后重新推演；中文名可填在选填格裡，僅作回顯、不参与計算。',
  '正在逐字取值、约简六个核心数并排布两张九宫…': '正在逐字取值、約簡六個核心數并排布兩张九宫…',
  白话总论: '白話總論',
  核心本命数仪表盘: '核心本命数仪表盘',
  '六个核心数 · 各自带约简账本': '六個核心数 · 各自带約簡賬本',
  姓名天赋九宫: '姓名天賦九宫',
  '来自姓名 · 业力课 {{count}} 个': '來自姓名 · 業力課 {{count}} 個',
  生辰洛书九宫: '生辰洛書九宫',
  '来自生日 · 八平面贯通 {{count}} 条': '來自生日 · 八平面贯通 {{count}} 條',
  顶峰与挑战阶梯: '顶峰與挑战階梯',
  '四程顶峰 · 四项挑战': '四程顶峰 · 四項挑战',
  个人年月日周期: '個人年月日周期',
  '基准日 {{date}}': '基準日 {{date}}',
  字母映射与逐字透视: '字母映射與逐字透视',
  '{{mapCols}} 列映射 · 姓名 {{letters}} 个字母': '{{mapCols}} 列映射 · 姓名 {{letters}} 個字母',
  公历生日: '公曆生日',
  '数字命理是西方体系，公历是其原生输入（spec §4.2）': '數字命理是西方体系，公曆是其原生輸入（spec §4.2）',
  基准日周岁: '基準日周岁',
  '基准日早于生日': '基準日早于生日',
  '基准日早于生日时如实留空，不填负数或 0': '基準日早于生日時如實留空，不填負数或 0',
  参与字母: '参与字母',
  跳过字符: '跳过字符',
  字母值总和: '字母值總和',
  '恒等于元音和 + 辅音和': '恆等于元音和 + 辅音和',
  '{{count}} 个': '{{count}} 個',
  '推演对象 · SUBJECT': '推演對象 · SUBJECT',
  'Y 元音判定 · 计入元音': 'Y 元音判定 · 計入元音',
  'Y 元音判定 · 计为辅音': 'Y 元音判定 · 計為辅音',
  '元音和 {{vowel}} + 辅音和 {{consonant}} = 全字母和 {{total}}。这三个是约简前的总和，各自约简后才是灵魂冲动数、人格面具数与表达数，约简过程印在对应卡片的账本里。':
    '元音和 {{vowel}} + 辅音和 {{consonant}} = 全字母和 {{total}}。這三個是約簡前的總和，各自約簡後才是灵魂推動数、人格面具数與表达数，約簡過程印在對應卡片的賬本裡。',
  '有 {{count}} 个字符不参与计算（去重后：': '有 {{count}} 個字符不参与計算（去重後：',
  '）。毕达哥拉斯映射只定义在拉丁字母表上，其余字符如实报出、不折算成 0（决策 8）。':
    '）。毕达哥拉斯映射只定义在拉丁字母表上，其余字符如實报出、不折算成 0（決策 8）。',
  '生命灵数的相加行未落在 13 / 14 / 16 / 19 上，故无业力债。只有相加行会判：年份逐位约简的途中也会路过 19，那里多报一个就是报出来源本人也没报的债（spec §6.8）。':
    '生命灵数的相加行未落在 13 / 14 / 16 / 19 上，故无业力债。只有相加行会判：年份逐位約簡的途中也会路过 19，那裡多报一个就是报出來源本人也没报的债（spec §6.8）。',
  '业力债 · KARMIC DEBT': '业力债 · KARMIC DEBT',

  // WesternNatal page
  '本命星盘与时空推运': '本命星盘與時空推運',
  '精确计算本命四轴（ASC/MC/DES/IC）与十大主星落座落宫、主要相位容许度及元素形态分布。示例：2000-01-01 12:00 · 格林尼治 (51.4769, -0.0005) · UTC 0。':
    '精确计算本命四轴（ASC/MC/DES/IC）与十大主星落座落宫、主要相位容许度及元素形态分布。示例：2000-01-01 12:00 · 格林尼治 (51.4769, -0.0005) · UTC 0。',
  '重构星历中…': '重構星曆中…',
  即刻重构星历: '即刻重構星曆',
  '黄道基准：热带黄道 (Tropical)': '黃道基準：熱帶黃道 (Tropical)',
  '时区留空时按出生经度推算 UTC 偏移（每 15° ≈ 1 小时）。': '時區留空時依出生經度推算 UTC 偏移（每 15° ≈ 1 小時）。',
  'ASC 极敏感：约每 4 分钟误差 ≈ 1° 上升点。': 'ASC 極敏感：約每 4 分鐘誤差 ≈ 1° 上升點。',
  '分宫制 / HOUSE SYSTEM': '分宫制 / HOUSE SYSTEM',
  分宫制: '分宫制',
  '时区 / UTC OFFSET': '時區 / UTC OFFSET',
  小时: '小時',
  '自动（按经度）': '自動（依經度）',
  'UTC 时区偏移（小时）': 'UTC 時區偏移（小時）',
  '正在依瑞士星历重构本命天球…': '正在依瑞士星曆重構本命天球…',
  天球黄道命盘轮图: '天球黃道命盤輪圖',
  元素与形态分布: '元素與形態分布',
  十二宫头: '十二宫頭',
  本命三巨头核心图腾: '本命三巨头核心圖騰',
  十大主星与交点: '十大主星與交點',
  关键相位网格: '關鍵相位網格',
  白话详解: '白話詳解',
  '本命星盘 · NATAL CHART': '本命星盤 · NATAL CHART',
  '日{{sun}} · 月{{moon}} · 升{{asc}}': '日{{sun}} · 月{{moon}} · 升{{asc}}',
  '当地时：': '當地時：',
  '世界时：': '世界時：',
  '儒略日：': '儒略日：',
  '坐标：': '座標：',
  '分宫制：': '分宫制：',
  '时区 {{offset}}（{{source}}）': '時區 {{offset}}（{{source}}）',
  显式输入: '顯式輸入',
  经度推算: '經度推算',
  '相位图例 / ASPECTS': '相位圖例 / ASPECTS',
  普拉西度: '普拉西度',
  科赫: '科赫',
  雷吉奥蒙塔努斯: '雷吉奧蒙塔努斯',
  等宫制: '等宫制',
  全星座: '全星座',
  '普拉西度 Placidus': '普拉西度 Placidus',
  '科赫 Koch': '科赫 Koch',
  '雷吉奥蒙塔努斯 Regiomontanus': '雷吉奧蒙塔努斯 Regiomontanus',
  '等宫制 Equal': '等宫制 Equal',
  '全星座 Whole Sign': '全星座 Whole Sign',
  合相: '合相',
  六合: '六合',
  刑相: '刑相',
  拱相: '拱相',
  冲相: '冲相',
  相位: '相位',
};

const en: MessageDict = {
  // SiteHeader + brand
  'Destiny 测算大厅': 'Destiny Divination Hall',
  主导航: 'Main navigation',
  发现: 'Discover',
  从问题开始: 'Start with a question',
  报告样例: 'Sample report',
  探索全部体系: 'Explore all systems',
  我的档案: 'My profiles',
  打开体系导航: 'Open system navigation',
  关闭体系导航: 'Close system navigation',
  '以你熟悉的方式，开始探索。': 'Begin in a language you already know.',
  全体系导航: 'Full system navigation',
  快捷入口: 'Quick access',
  '观己 · 知时 · 懂相处': 'Know thyself · Read the times · Meet others',

  // Primary nav
  测算大厅: 'Divination Hall',
  八字排盘: 'BaZi Chart',
  西洋占星: 'Western Astrology',
  塔罗神谕: 'Tarot Oracle',
  周易六爻: 'I Ching',

  // Secondary nav groups
  华夏术数: 'Chinese Arts',
  西洋秘学: 'Western Esoterica',
  吠陀与北欧: 'Vedic & Norse',

  // Secondary nav items
  八字命理: 'BaZi Destiny',
  岁运推演: 'Annual Cycles',
  紫微斗数: 'Zi Wei Dou Shu',
  奇门遁甲: 'Qi Men Dun Jia',
  文王六爻: 'King Wen I Ching',
  梅花易数: 'Plum Blossom Numerology',
  八字合婚: 'BaZi Compatibility',
  五格姓名学: 'Name Numerology',
  本命星盘: 'Natal Chart',
  行运推运: 'Transits & Progressions',
  双人合盘: 'Synastry',
  经典塔罗: 'Classic Tarot',
  雷诺曼: 'Lenormand',
  卡巴拉: 'Kabbalah',
  毕氏灵数: 'Pythagorean Numerology',
  吠陀乔蒂什: 'Vedic Jyotish',
  北欧卢恩: 'Norse Runes',

  // SiteFooter
  合规免责声明: 'Compliance Disclaimer',
  '本平台所有命理排盘、星历计算及推演结果均基于数理模型与民俗哲学古籍整理，结果仅供娱乐与文化参考，不构成任何医疗、法律、财务或重大人生命运决策建议。':
    'All divination charts, ephemeris calculations, and derived readings on this platform are built from mathematical models and classical folk-philosophy texts. Results are for entertainment and cultural reference only, and do not constitute medical, legal, financial, or major life-decision advice.',
  了解排盘依据与隐私保存: 'How readings are computed and where data lives',
  天文与时空基准: 'Ephemeris & True Solar Time',
  '以权威星历推算行星黄经与宫头；真太阳时按经度时差（每度 4 分钟）与均时差动态校准，经纬度解析全球坐标。':
    'Planetary ecliptic longitudes and house cusps come from an authoritative ephemeris. True solar time is calibrated from longitude offset (4 minutes per degree) and the equation of time; latitude/longitude resolve globally.',
  古籍历法溯源: 'Classical Provenance',
  '依权威历法严谨推算二十四节气换气定柱；卦爻辞锚定《周易》通行本原文，杜绝虚构易辞与生搬硬造的星盘断语。':
    'The 24 solar terms and pillar boundaries follow an authoritative Chinese calendar; hexagram and line texts are anchored to the received I Ching. No fabricated line judgments, no forced astrology verdicts.',
  隐私与天机安全: 'Privacy & Statelessness',
  '普通排盘不在服务端保存。我的档案、卢恩秘匣和主题偏好保存在本机浏览器；报告输入在当前标签页暂存。人工确认交付的报告会在服务端保存固定版本直至到期清理。下钻链接可能包含生辰和地点，请勿公开转发；浏览器历史、下载文件和服务访问日志需分别管理。':
    'Ordinary charts are never stored server-side. My profiles, the Rune Vault, and theme preferences live in your browser; report inputs sit in the current tab only. Reports delivered through manual confirmation are kept server-side as a fixed snapshot until their expiry cleanup. Drill-down links may embed birth data and location — please do not forward them publicly. Browser history, downloaded files, and server access logs are managed separately.',

  // LocalDataControls
  管理本机档案与收藏: 'Manage local profiles and saved items',
  '档案、卢恩收藏只存本机，没有自动加密或云端备份。清除会删除这些记录及当前报告输入，不会删除下载文件或浏览器历史。':
    'Profiles and the Rune Vault live only on this device — no automatic encryption, no cloud backup. Clearing removes them along with any current report input, but never touches downloaded files or browser history.',
  导出本机记录: 'Export local data',
  清除本机记录: 'Clear local data',
  '请先导出需要保留的记录。确认清除所有本机档案和卢恩收藏？':
    'Export anything worth keeping first. Clear all local profiles and the Rune Vault?',
  确认清除: 'Confirm clear',
  取消: 'Cancel',
  '导出文件可能含姓名、生辰与问题记录，请妥善保管。':
    'The exported file may contain names, birth data, and your question history — store it safely.',
  '无法导出，请检查浏览器的存储权限。': 'Export failed — check the browser storage permissions.',
  '清除未能完成，请使用浏览器的网站数据设置。':
    'Clear did not complete — use the browser site-data settings instead.',

  // ThemeToggle
  切换为曜石深色: 'Switch to obsidian dark',
  切换为暖纸白: 'Switch to warm paper',

  // PortalHero
  '把古老的智慧，': 'Ancient wisdom,',
  '读成自己的答案。': 'read as an answer of your own.',
  '从了解自己，到读懂一段关系。': 'From understanding yourself to reading a relationship.',
  '把复杂的排盘，整理成你看得懂、用得上的生活观察。':
    'Chart-heavy output, distilled into everyday observations you can actually use.',
  从你关心的问题开始: 'Start with the question you have',
  先读一份真实样例: 'Read a real sample first',
  有据可查的排盘: 'Charts you can verify',
  读得懂的解读: 'Readings you can follow',
  留给自己的选择: 'Choices you keep',
  '天体轨道装饰，不代表实际星体位置': 'Decorative orbital rings — not actual planetary positions',
  每一份排盘: 'Every chart',
  都是一次重新认识自己的起点: 'is a fresh place to meet yourself again',
  开始八字排盘: 'Open the BaZi chart',

  // PortalPage
  全部体系: 'All systems',
  '先读结论，再看它从何而来。': 'Read the takeaway first, then its provenance.',
  '排盘依据、传统解释与生活建议，分层阅读。你可以参考，也可以保留不同的看法。':
    'Chart basis, traditional interpretation, and practical suggestions are layered so you can read only what you want. Take them as reference, or hold a different view.',
  '探索全部 {{count}} 个体系': 'Explore all {{count}} systems',
  '找到你熟悉的那一种视角。': 'Find the lens you already trust.',
  体系类目筛选: 'System category filter',
  了解本次授时与历算基准: 'Time and calendar basis for this session',

  // QuestionEntries
  '此刻，你更想了解什么？': 'Right now, what do you want to know?',
  '不必先懂术语，从一个真实的关心开始。':
    'No jargon required — start from a question that actually matters.',
  '我怎样，才能更好地用自己？': 'How can I work better with who I am?',
  关于自己: 'About yourself',
  '看见驱动力、压力反应与相处需求，找到适合自己的节奏。':
    'See your drivers, stress responses, and relational needs — then pick a pace that fits.',
  '我们为什么亲近，又为何摩擦？': 'Why we click, and why we grind.',
  关于关系: 'About the relationship',
  '从双方的需求与差异出发，把抽象的互补读成可讨论的议题。':
    'Start from each side\'s needs and differences; turn abstract "complementarity" into discussable topics.',
  '下一阶段，我想怎样安排？': 'How should I arrange the next chapter?',
  关于节奏: 'About timing',
  '了解年度与流月的传统解读，再结合自己的现实计划做取舍。':
    'Read the traditional year and month cycles, then decide against your real plans.',
  开始探索: 'Start exploring',

  // Portal system catalogue — nameZh (entries not already covered by nav.ts)
  '西洋本命星盘': 'Western Natal Chart',
  '经典塔罗神谕': 'Tarot Oracle',
  '雷诺曼神谕': 'Lenormand Oracle',
  '行运次限推运': 'Transits & Progressions',
  '毕达哥拉斯灵数': 'Pythagorean Numerology',
  '卡巴拉生命之树': 'Kabbalistic Tree of Life',
  '合盘与相契度': 'Synastry & Composite',
  '北欧卢恩符文': 'Elder Futhark Runes',

  // Portal system catalogue — blurbs, tags, CTAs
  '《渊海子平》正宗四柱推演，以天干地支五行生克制化，厘定身强身弱与十神大运走势。':
    'Classical four-pillar reading from Yuan Hai Zi Ping — stems, branches, and the five-phase balance shape strong/weak daymasters and the Ten-Gods luck cycle.',
  十神精微: 'Ten-Gods detail',
  真太阳时: 'True solar time',
  立即排盘: 'Cast chart now',
  '文王六十四卦精研，京房纳甲卦变。铜钱三掷起卦，定世应六亲六神，附通行本卦爻辞原文。':
    'King Wen\'s 64 hexagrams with Jing Fang na-jia transformations. Three-coin casting fixes world/response, six relatives, and six spirits; received I Ching text included.',
  古籍原文: 'Classical text',
  世应动爻: 'World/response & moving lines',
  摇铜求卦: 'Cast with coins',
  '基于普拉西德分宫制与精密黄道，解构日月升、十行星落座落宫、相位与守护格局。':
    'Placidus houses on the precise zodiac — Sun, Moon, Ascendant, ten planets by sign and house, aspects, and rulership patterns.',
  瑞士星历: 'Swiss Ephemeris',
  精密相位: 'Precise aspects',
  测绘星图: 'Chart the sky',
  '78 张伟特系大小阿卡纳原生牌阵，凯尔特十字、时间之流与关系牌阵深度洞察。':
    '78-card Rider-Waite-Smith deck with native spreads — Celtic Cross, Flow of Time, and a relational layout.',
  洗牌抽卡: 'Shuffle & draw',
  牌阵解析: 'Spread reading',
  开启抽牌: 'Draw cards',
  '十二宫垣星曜罗列，紫微天府南北斗交辉，四化飞星直断流年大限气数。':
    'Twelve palaces laid out with Zi Wei and Tian Fu across the Northern and Southern Dipper; the Four Transformations fly through annual and decadal luck.',
  十二宫四化体系: 'Twelve-palace Four Transformations',
  排定命盘: 'Cast chart',
  '帝王之术，九星八门八神九宫定局，天地人神四盘交错，谋定决策时空场。':
    'The emperor\'s art — nine stars, eight gates, eight spirits across nine palaces; heaven, earth, human and divine plates interlock into a decision space.',
  时家转盘法: 'Hour-school rotating plate',
  起局排盘: 'Set the board',
  '邵康节灵应法门，随感随应、物象心机，报数方位声色皆可起体用卦象。':
    'Shao Yong\'s responsive method — a number, direction, sound, or sight triggers substance/response hexagrams.',
  体用互变论: 'Substance/response transformation',
  起卦断体用: 'Cast & judge',
  '康熙字典原笔画核定，天格地格人格总格外格相生相克数理吉凶。':
    'Stroke counts verified against the Kangxi Dictionary; heaven, earth, person, total, and outer grids read through their generative/conflicting numerology.',
  '81 数理吉凶表': '81-number fortune table',
  核定笔画: 'Verify strokes',
  '欧式 36 张生活微观象征图画，大画卷（Grand Tableau）全景排布直析吉凶线索。':
    '36 European everyday-symbol cards; the Grand Tableau lays out the full scene and reads fortune lines directly.',
  '36 张全景大阵': '36-card Grand Tableau',
  洗牌抽牌: 'Shuffle & draw',
  '外行星过境、太阳弧与次限法双重时间轴对碰，动态叠加本命盘。':
    'Outer-planet transits, solar arcs, and secondary progressions collide on two time axes layered over the natal chart.',
  多盘动态重叠: 'Multi-chart dynamic overlay',
  叠加行运盘: 'Overlay transit chart',
  '生命灵数、表达数与灵魂冲动数，以数字震动频率洞察天赋潜能与流年周期。':
    'Life Path, Expression, and Soul Urge — numerical vibration maps talent, potential, and the annual cycle.',
  双九宫矩阵: 'Twin nine-box matrix',
  推演灵数: 'Derive numbers',
  '十原质（Sephiroth）与 22 条神圣路径，对应塔罗大阿卡纳与希伯来字母创世密源。':
    'Ten Sephiroth and 22 sacred paths mapped to Tarot Major Arcana and the Hebrew creative letters.',
  原质路径升华: 'Sephiroth & path ascent',
  探索生命之树: 'Explore the Tree',
  '双人本命比较盘（Synastry）人对人相位、短弧中点组合盘（Composite）与相契度总分账本，直击两人因缘契合力学。':
    'Person-to-person Synastry aspects, the Composite midpoint chart, and an aggregate affinity ledger — the mechanics of a two-person bond.',
  双轮合盘: 'Dual-wheel synastry',
  相契度账本: 'Affinity ledger',
  开始合盘: 'Start synastry',
  '基于恒星黄道（Lahiri Ayanamsa）及 27 宿（Nakshatras），推演业力因果与达夏大运。':
    'Sidereal zodiac on the Lahiri ayanamsa with the 27 nakshatras; karmic patterns unfold through Vimshottari dashas.',
  '南印 / 北印方盘': 'South / North Indian charts',
  排定星盘: 'Cast chart',
  '24 枚古老弗萨克字符石，序位据 Kylver 石碑；单枚启示、诺伦三女神运命之阵与卢恩十字，另可启用现代增补的空白符。':
    '24 Elder Futhark rune stones ordered per the Kylver stem; single-stone draws, the Nornir three-lady web of fate, and the Runic Cross — with the optional modern blank rune.',
  三种牌阵: 'Three spreads',
  全典检索: 'Full codex search',
  掷符铸石: 'Cast the runes',

  // Router fallback / NotFound / RouteError
  '正在打开页面…': 'Opening page…',
  迷失星域: 'Lost in the Starfield',
  '未找到该路径对应的秘术体系，请返回测算大厅重新起盘。':
    'This path does not match any tradition on the map. Return to the Divination Hall to begin again.',
  'ERROR 404': 'ERROR 404',
  返回测算大厅: 'Back to the Hall',
  '页面刚刚更新，请重新载入。': 'The page was just updated — please reload.',
  '这个页面暂时无法打开。': 'This page cannot be opened right now.',
  '已保存的本机档案不会因此删除。你可以重试，或回到首页继续探索。':
    'Your saved local profiles are not deleted by this. Retry, or head back home to keep exploring.',
  重新载入: 'Reload',
  回到首页: 'Back to home',

  // --- Phase 2.1 · shared UI chrome ---
  // InputBar internals
  公历: 'Solar',
  农历: 'Lunar',
  历法: 'Calendar',
  '把当前生辰与出生地存入本地档案': 'Save the current birth data and location to a local profile',
  填写生辰后即可存入档案: 'Fill in the birth data to save it as a profile',
  存入档案: 'Save profile',
  '生辰（精准至分）': 'Birth date & time (to the minute)',
  '出生基准地（全球坐标）': 'Birth location (global coordinates)',
  '填写出生日期、时间并完成经纬度定位后即可排盘。':
    'Complete the birth date, time, and coordinates to cast the chart.',
  '填写出生日期、时间并完成定位后即可排盘。':
    'Complete the birth date, time, and location to cast the chart.',

  // LocationField
  '搜索城市，或下方直接填写经纬度': 'Search a city, or enter latitude/longitude below',
  出生城市搜索: 'Birth-city search',
  清除地点: 'Clear location',
  '城市查询服务暂时不可用，请检查后端服务是否启动，或在下方手动填写经纬度。':
    'The city lookup service is unavailable — check the backend, or enter coordinates manually below.',
  重试查询: 'Retry lookup',
  '未匹配到「{{term}}」，请在下方手动填写经纬度。':
    'No match for “{{term}}” — enter coordinates manually below.',
  纬度: 'Latitude',
  经度: 'Longitude',
  手动坐标: 'Manual coordinates',

  // DateTimeField unit labels + aria default
  年: 'Y',
  月: 'M',
  日: 'D',
  时: 'h',
  分: 'm',
  出生: 'Birth',

  // TrueSolarTimeBadge
  '填写出生日期、时间并定位后，此处按经度与均时差显示真太阳时校准。':
    'Once birth date, time, and location are set, the true-solar-time correction appears here (from longitude offset and equation of time).',
  真太阳时校准定盘: 'True Solar Time calibrated',
  标准时: 'Standard time',
  '正在按经度与均时差推算…': 'Deriving from longitude and equation of time…',
  '真太阳时服务暂不可用。': 'True solar time service is unavailable.',
  '等待计算…': 'Awaiting calculation…',
  校正: 'Offset',

  // VerdictCard
  综合结论: 'Overall verdict',
  星: 'star',

  // ProfilePicker
  选择档案: 'Pick a profile',
  男: 'M',
  女: 'F',
  未填生辰: 'No birth data yet',
  '不使用档案（清空）': 'Do not use a profile (clear)',
  管理档案: 'Manage profiles',
  '还没有档案。先去建一个，测算时就能一键填充。':
    'No profiles yet. Create one and future readings will fill in with a single click.',
  去创建档案: 'Create a profile',

  // ProfileEditor dialog
  编辑档案: 'Edit profile',
  新建档案: 'New profile',
  关闭: 'Close',
  '仅保存在本机浏览器，不上传服务器，可随时编辑或删除。':
    'Stored only in this browser — never uploaded. Edit or delete at any time.',
  '档案名（必填）': 'Profile name (required)',
  '如 我自己 / 父亲 / 长子': 'e.g. Me / Father / Eldest son',
  给自己起个称呼: 'Give yourself a nickname',
  档案名: 'Profile name',
  '姓氏（供姓名学拆分）': 'Surname (for name numerology)',
  '如 陸': 'e.g. Lu',
  姓氏: 'Surname',
  名字: 'Given name',
  '如 青玄': 'e.g. Qingxuan',
  性别: 'Gender',
  出生日期: 'Birth date',
  出生时间: 'Birth time',
  '出生地（全球坐标）': 'Birth location (global coordinates)',
  保存修改: 'Save changes',

  // Page-level InputBar chrome (badges, submit states)
  权威历算: 'Authoritative calendar',
  排盘中: 'Casting…',
  开始排盘: 'Cast the chart',
  '造向（性别）': 'Direction (gender)',
  '命主称谓（可选，仅回显）': 'Chart owner (optional, display only)',
  '如：示例命主': 'e.g. Sample subject',
  '真太阳时校正（推荐）': 'True solar time correction (recommended)',
  '正在依据真太阳时排定四柱…': 'Deriving the four pillars from true solar time…',
  本命使用说明书: 'Owner\'s Manual for This Chart',
  四柱八字精算排盘: 'Four Pillars BaZi — Precision Chart',
  '真太阳时经度校正与节气精确交节，一次排定干支、十神、藏干、纳音、身强身弱与大运流年。示例：1988-02-15 23:30 · 成都 · 乾造（男）。':
    'Longitude-corrected true solar time and precise solar-term boundaries resolve stems, branches, Ten-Gods, hidden stems, nayin, strong/weak daymaster, and luck cycles in one cast. Example: 1988-02-15 23:30 · Chengdu · Male.',
  四柱命造干支矩阵: 'Four-Pillars Stems-and-Branches Matrix',
  四柱: 'Four Pillars',
  地支藏干权重与十神: 'Branch Hidden-Stem Weights & Ten-Gods',
  '藏干十神': 'Hidden Stems',
  五行能量量化分布: 'Five-Phase Energy Distribution',
  五行: 'Five Phases',
  日主强弱与格局: 'Daymaster Strength & Structure',
  强弱格局: 'Strength & Structure',
  '用神三法（扶抑 / 通关 / 调候）': 'Yongshen Three Methods (Support/Control · Bridge · Climate)',
  '用神三法': 'Yongshen (Useful God)',
  神煞命中: 'Shen-Sha Hits',
  神煞: 'Shen-Sha',
  '刑冲合害破与合会局': 'Punishment/Clash/Combination/Harm/Destruction & Branch Frames',
  刑冲合害: 'Relations',
  大运流变时间轴: 'Luck Pillars Timeline',
  大运: 'Luck Pillars',
  六维详批: 'Six-Dimension Deep Read',
  命盘分区: 'Chart sections',
  推演此造岁运流年: 'Run annual cycles for this chart',
  以此造合婚: 'Use this chart for marriage matching',
  '当前大运 ·': 'Current luck pillar ·',
  '此运与四柱之间未构成伏吟或反吟。': 'This pillar forms neither fu-yin nor fan-yin with the four pillars.',
  岁: ' yrs',
  四柱命造: 'Four-Pillar Chart',
  生肖: 'Zodiac',
  日元: 'Day Master',
  命宫: 'Life Palace',
  胎元: 'Conception Pillar',
  参照日: 'Reference date',

  // ReportEntryBar internals
  '本盘已排定，可进一步生成《{{productName}}》——按问题组织的深度解读报告。':
    'This chart is cast — generate the “{{productName}}” for a question-organised in-depth read.',
  生成报告: 'Generate the report',

  // BaziNatal · ChartSummary heading + colon labels + tst variants
  '四柱命造 · FOUR PILLARS': 'FOUR PILLARS',
  '农历：': 'Lunar:',
  '标准时：': 'Standard:',
  '经度：': 'Longitude:',
  '真太阳时 {{tst}}（校正 {{offset}} 分）': 'True solar time {{tst}} (offset {{offset}} min)',
  '未校正（标准时直排）': 'Uncorrected (standard time)',

  // --- Phase 2.3 · Tarot / Lenormand / PlumBlossom / Zhouyi page chrome ---
  // Tarot
  '正在洗牌布阵…': 'Shuffling and laying out the spread…',
  已全部翻开: 'All revealed',
  翻开全部: 'Reveal all',
  '点选任意牌张即可翻开并展开详解；逆位牌以颠倒方向呈现。':
    'Click any card to flip it face-up and open its full reading; reversed cards render upside-down.',
  牌阵盘面: 'Spread Board',
  牌义详解: 'Card Meanings',
  围绕你选择的主题: 'On Your Chosen Topic',
  综合解读: 'Integrated Reading',

  // Lenormand
  '正在洗牌抽牌，铺陈牌阵…': 'Shuffling and drawing cards, laying out the spread…',
  '第 {{n}} 位 ·': 'Position {{n}} ·',
  张: 'cards',
  所问之事: 'The question',
  '点击牌阵中任意一张牌，查看其完整牌义。':
    'Click any card in the spread to see its full meaning.',
  核心牌义: 'Core meaning',
  '名词核心：': 'Noun core:',
  '；作后牌修饰前牌时：': '; as a following card it modifies the previous one:',
  牌阵布局: 'Spread Layout',
  组合直读透镜: 'Pair-Reading Lens',
  综合判读: 'Synthesis',

  // PlumBlossom
  '正在起卦，推演体用互变…': 'Casting the hexagram and deriving ti/yong/hu/bian…',
  '本卦 → 变卦 · PRIMARY TO CHANGED': 'Primary → Changed hexagram',
  '起卦推演 · DERIVATION': 'Cast derivation',
  所占之事: 'The question',
  起卦时刻: 'Cast time',
  月令卦气: 'Seasonal qi',
  当令: 'in command',
  体卦: 'Ti (Body) hexagram',
  用卦: 'Yong (Function) hexagram',
  '互卦 · 事之中段': 'Hu hexagram · middle of the matter',
  '变卦 · 事之归宿': 'Changed hexagram · where the matter settles',
  卦象三盘: 'Three-hexagram boards',
  体用生克: 'Ti-Yong Generation/Restraint',
  吉凶指数: 'Fortune Index',
  互变推演: 'Hu & Bian Derivation',

  // Zhouyi
  '正在起卦排盘，推演纳甲六亲…': 'Casting and arranging najia & six relations…',
  整卦白话: 'Whole-hexagram Plain Read',
  纳甲六亲盘: 'Najia & Six-Relations Board',
  起卦记录: 'Cast Ledger',
  变卦: 'Changed Hexagram',
  '本卦动爻阴阳互变得变卦，示事之趋向。':
    'Yin/yang inversion of the moving lines in the primary hexagram yields the changed hexagram — where the matter leans.',
  '六爻安静，本卦无动爻，故无变卦。占断以本卦卦辞与世应为主。':
    'All six lines are still — no moving line, so no changed hexagram. Base the read on the primary hexagram\'s statement and shi/ying.',
  互卦: 'Mutual Hexagram',
  '取本卦二三四爻为下卦、三四五爻为上卦，得互卦，示事之中段。':
    'Take lines 2-3-4 as the lower trigram and 3-4-5 as the upper — this yields the hu hexagram, the middle of the matter.',
  卦爻辞: 'Hexagram & Line Statements',
  '六爻安静 · 无变卦': 'All lines still · no changed hexagram',
  '{{count}} 爻动': '{{count}} moving lines',
  日柱: 'Day pillar',
  本卦宫: 'Primary palace',
  动爻: 'Moving lines',
  无: 'None',
  动: ' moving',

  // --- Phase 2.4 · Qimen / Ziwei page chrome ---
  // Qimen
  '正在起局，布地盘、转九星八门八神…': 'Setting the board — arranging the earth plate, rotating the nine stars, eight doors, eight spirits…',
  全局白话: 'Board Overview',
  洛书九宫盘: 'Luoshu Nine-Palace Board',
  九宫白话: 'Nine Palaces in Plain Words',
  '定局 · JU DETERMINATION': 'Ju determination',
  值符: 'Duty Star',
  值使: 'Duty Door',
  落: ' lands in ',
  宫: ' palace',
  年柱: 'Year pillar',
  月柱: 'Month pillar',
  时柱: 'Hour pillar',
  时辰旬首: 'Xun head of the hour',
  '{{xs}}（遁{{yi}}）': '{{xs}} (Dun {{yi}})',
  旬空: 'Xun void',
  驿马: 'Post horse',
  用事时刻: 'Matter time',
  占问事项: 'The matter asked',

  // Ziwei
  '正在安星排盘，布列十二宫垣…': 'Seating the stars and arranging the twelve palaces…',
  全盘白话: 'Whole-Chart Plain Read',
  十二宫命盘: 'Twelve-Palace Natal Board',
  十二宫白话: 'Twelve Palaces in Plain Words',
  '紫微斗数命盘 · ZI WEI DOU SHU': 'Zi Wei Dou Shu natal board',
  造向: 'Direction',
  命主: 'Life lord',
  身主: 'Body lord',
  紫微: 'Zi Wei',
  天府: 'Tian Fu',
  '（闰）': '(leap)',
  '身宫：': 'Body palace:',
  '大限：': 'Major limit:',
  岁起运: ' yrs to first limit',
  '历法：': 'Calendar:',

  // NorseRunes
  '正在铸石…': 'Casting the stones…',
  '{{count}} 枚石碑': '{{count}} stones',
  导出符印命谱: 'Export bindrune',

  // Report page
  '关系阶段（可选）': 'Relationship stage (optional)',
  暂不提供: 'Not provided',
  相识或交往: 'Acquaintance or dating',
  长期相处: 'Long-term together',
  修复分歧: 'Repairing rifts',
  '只用于组织沟通建议，不改变盘面计算。':
    'Used only to organise communication advice; chart calculations are unchanged.',
  报告起始日: 'Report start date',
  '不选则从今天开始，连续十二个月。': 'Defaults to today, covering the next twelve months.',
  返回发现: 'Back to Discover',
  '真实计算样例 · 非个人测评': 'Real computation sample · not a personal reading',
  私密报告交付: 'Private report delivery',
  报告预览: 'Report preview',
  '正在准备报告…': 'Preparing the report…',

  // Profiles page
  '把常用之人的生辰与出生地存成本地档案：八字、紫微、西洋占星等任一测算页点「选择档案」即可一键填充，测算后也可把当前输入一键存入。':
    'Save the birth data of the people you care about: on any divination page (BaZi, Zi Wei, Western natal, and so on) hit “Pick profile” to fill the console in one tap, or store the current inputs after casting.',
  '档案只写在你这台设备的浏览器里，不上传服务器，不随账号漫游，可随时编辑或删除。':
    'Profiles live only in this device\u2019s browser — no upload, no cross-account sync, editable or deletable at any time.',
  '{{count}} 份档案 · 本机存储': '{{count}} profiles · stored locally',
  还没有档案: 'No profiles yet',
  '点击「新建档案」录入第一位家人或朋友，之后在任何测算页都能从「选择档案」一键带入其生辰。':
    'Click “New profile” to add a family member or friend; from then on any divination page can fill in their birth data via “Pick profile”.',
  新建第一份档案: 'Create your first profile',
  未填性别: 'Gender not set',
  '更新于 {{date}}': 'Updated {{date}}',
  编辑: 'Edit',
  确认删除: 'Confirm delete',
  删除: 'Delete',

  // Kabbalah page
  '正在展开生命之树…': 'Unfurling the Tree of Life…',
  'TREE OF LIFE · {{sep}} 原质 · {{path}} 路径': 'TREE OF LIFE · {{sep}} Sephiroth · {{path}} Paths',
  '点选原质或路径，展开象征对应': 'Click a Sephirah or Path to reveal its symbol set.',
  生命之树: 'Tree of Life',
  全树白话: 'Whole-Tree Plain Read',
  '原质 / 路径详解': 'Sephirah / Path in depth',
  'gematria 数理折入': 'Gematria fold-in',
  '十原质 · SEPHIROTH': 'Ten Sephiroth',
  '22 路径 · PATHS': '22 Paths',
  '生命之树是卡巴拉的核心图示：神圣之光自':
    'The Tree of Life is Kabbalah\u2019s central diagram: divine light descends from ',
  '王冠（Kether）': 'the Crown (Kether)',
  '逐级降落，经': ', stepping through ',
  '十原质（Sephiroth）': 'the ten Sephiroth',
  '显化为物质世界的': ', into the material ',
  '王国（Malkuth）': 'Kingdom (Malkuth)',
  '；十原质之间由 22 条路径相连，每条路径对应一个希伯来字母、一张塔罗大阿卡纳与一组行星／星座／元素。点选任意原质或路径，即可查其黄金黎明（Golden Dawn）体系下的完整对应。':
    '; the ten are joined by 22 Paths, each tied to a Hebrew letter, a Tarot trump and a set of planetary / zodiacal / elemental correspondences. Click any Sephirah or Path to reveal its full Golden Dawn attribution.',

  // Name page
  选档案填姓名: 'Pick a profile for the name',
  '正在核定康熙笔画并推演五格…': 'Verifying Kangxi stroke counts and deriving the five grids…',
  字级溯源: 'Per-character provenance',
  五格: 'Five grids',
  三才: 'Three powers',
  综合指数: 'Overall index',
  康熙笔画核定: 'Kangxi stroke verification',
  五格剖象全景图谱: 'Five-Grid Panorama',
  三才配置深度研判: 'Three-Powers configuration in depth',
  姓名综合气象指数: 'Name overall meteoric index',
  姓名学分区: 'Name-analysis sections',
  '核定姓名 · RESOLVED': 'RESOLVED NAME',
  '以下字的康熙笔画不在本语料范围内，相关五格与指数不予推算：':
    'Kangxi stroke counts for the following characters are outside this corpus; the related grids and index are withheld:',

  // Numerology page
  出错字段: 'Offending field',
  '把姓名换成拼音或英文名后重新推演；中文名可填在选填格里，仅作回显、不参与计算。':
    'Retry with the name in pinyin or an English form; the optional Chinese name is only echoed back and does not enter the computation.',
  '正在逐字取值、约简六个核心数并排布两张九宫…': 'Deriving per-letter values, reducing the six core numbers and laying out the two nine-palace grids…',
  白话总论: 'Plain Overview',
  核心本命数仪表盘: 'Core Number Dashboard',
  '六个核心数 · 各自带约简账本': 'Six core numbers · each with its own reduction ledger',
  姓名天赋九宫: 'Name Talent Nine-Palace',
  '来自姓名 · 业力课 {{count}} 个': 'From the name · {{count}} karmic lessons',
  生辰洛书九宫: 'Birth Lo-Shu Nine-Palace',
  '来自生日 · 八平面贯通 {{count}} 条': 'From the birthday · {{count}} of eight planes completed',
  顶峰与挑战阶梯: 'Pinnacles & Challenges Ladder',
  '四程顶峰 · 四项挑战': 'Four pinnacles · four challenges',
  个人年月日周期: 'Personal Year / Month / Day',
  '基准日 {{date}}': 'Reference date {{date}}',
  字母映射与逐字透视: 'Letter map & per-character view',
  '{{mapCols}} 列映射 · 姓名 {{letters}} 个字母': '{{mapCols}} mapped columns · {{letters}} letters in the name',
  公历生日: 'Solar birthday',
  '数字命理是西方体系，公历是其原生输入（spec §4.2）': 'Numerology is a Western system; the solar calendar is its native input (spec §4.2).',
  基准日周岁: 'Age at reference date',
  '基准日早于生日': 'Reference date precedes the birthday',
  '基准日早于生日时如实留空，不填负数或 0': 'Left blank when the reference date precedes the birthday — never a negative or 0.',
  参与字母: 'Letters used',
  跳过字符: 'Skipped characters',
  字母值总和: 'Letter-value total',
  '恒等于元音和 + 辅音和': 'Always equals vowel sum + consonant sum.',
  '{{count}} 个': '{{count}}',
  '推演对象 · SUBJECT': 'SUBJECT',
  'Y 元音判定 · 计入元音': 'Y handling · counted as a vowel',
  'Y 元音判定 · 计为辅音': 'Y handling · counted as a consonant',
  '元音和 {{vowel}} + 辅音和 {{consonant}} = 全字母和 {{total}}。这三个是约简前的总和，各自约简后才是灵魂冲动数、人格面具数与表达数，约简过程印在对应卡片的账本里。':
    'Vowel sum {{vowel}} + consonant sum {{consonant}} = full letter sum {{total}}. These are the pre-reduction totals; their reduced forms are Soul Urge, Personality and Expression, each printed in the matching card’s ledger.',
  '有 {{count}} 个字符不参与计算（去重后：': '{{count}} characters do not enter the calculation (deduplicated: ',
  '）。毕达哥拉斯映射只定义在拉丁字母表上，其余字符如实报出、不折算成 0（决策 8）。':
    '). The Pythagorean map is defined only for the Latin alphabet; other characters are reported as they are, not folded to 0 (decision 8).',
  '生命灵数的相加行未落在 13 / 14 / 16 / 19 上，故无业力债。只有相加行会判：年份逐位约简的途中也会路过 19，那里多报一个就是报出来源本人也没报的债（spec §6.8）。':
    'The Life Path addition row did not land on 13 / 14 / 16 / 19, so no karmic debt. Only the addition row is judged: the digit-wise reduction of the year also passes through 19, and flagging it there would invent a debt the source itself does not report (spec §6.8).',
  '业力债 · KARMIC DEBT': 'KARMIC DEBT',

  // WesternNatal page
  '本命星盘与时空推运': 'Natal Chart & Astro-time',
  '精确计算本命四轴（ASC/MC/DES/IC）与十大主星落座落宫、主要相位容许度及元素形态分布。示例：2000-01-01 12:00 · 格林尼治 (51.4769, -0.0005) · UTC 0。':
    'Computes the four natal angles (ASC / MC / DES / IC), the sign-and-house landing of the ten major bodies, the orbs of the primary aspects, and the element / modality spread. Example: 2000-01-01 12:00 · Greenwich (51.4769, -0.0005) · UTC 0.',
  '重构星历中…': 'Recasting the ephemeris…',
  即刻重构星历: 'Cast the chart',
  '黄道基准：热带黄道 (Tropical)': 'Zodiac basis: Tropical',
  '时区留空时按出生经度推算 UTC 偏移（每 15° ≈ 1 小时）。':
    'Leaving the timezone blank derives the UTC offset from the birth longitude (roughly 1 h per 15°).',
  'ASC 极敏感：约每 4 分钟误差 ≈ 1° 上升点。':
    'ASC is very sensitive: about 4 minutes of time error ≈ 1° on the ascendant.',
  '分宫制 / HOUSE SYSTEM': 'House system',
  分宫制: 'House system',
  '时区 / UTC OFFSET': 'Timezone / UTC offset',
  小时: 'hours',
  '自动（按经度）': 'Auto (from longitude)',
  'UTC 时区偏移（小时）': 'UTC timezone offset (hours)',
  '正在依瑞士星历重构本命天球…': 'Recasting the natal sphere with the Swiss Ephemeris…',
  天球黄道命盘轮图: 'Celestial Zodiac Wheel',
  元素与形态分布: 'Element & Modality Balance',
  十二宫头: 'Twelve House Cusps',
  本命三巨头核心图腾: 'Big Three — Sun, Moon, Rising',
  十大主星与交点: 'Ten major bodies & lunar nodes',
  关键相位网格: 'Aspect matrix',
  白话详解: 'Plain Readings',
  '本命星盘 · NATAL CHART': 'NATAL CHART',
  '日{{sun}} · 月{{moon}} · 升{{asc}}': 'Sun {{sun}} · Moon {{moon}} · Rising {{asc}}',
  '当地时：': 'Local time:',
  '世界时：': 'UTC:',
  '儒略日：': 'Julian day:',
  '坐标：': 'Coordinates:',
  '分宫制：': 'House system:',
  '时区 {{offset}}（{{source}}）': 'Timezone {{offset}} ({{source}})',
  显式输入: 'explicit input',
  经度推算: 'derived from longitude',
  '相位图例 / ASPECTS': 'ASPECT LEGEND',
  普拉西度: 'Placidus',
  科赫: 'Koch',
  雷吉奥蒙塔努斯: 'Regiomontanus',
  等宫制: 'Equal',
  全星座: 'Whole Sign',
  '普拉西度 Placidus': 'Placidus',
  '科赫 Koch': 'Koch',
  '雷吉奥蒙塔努斯 Regiomontanus': 'Regiomontanus',
  '等宫制 Equal': 'Equal',
  '全星座 Whole Sign': 'Whole Sign',
  合相: 'Conjunction',
  六合: 'Sextile',
  刑相: 'Square',
  拱相: 'Trine',
  冲相: 'Opposition',
  相位: 'Aspect',
};

export const MESSAGES: Partial<Record<AppLocale, MessageDict>> = {
  'zh-Hant': zhHant,
  en,
};
