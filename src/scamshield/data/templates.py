"""
Message templates for the multilingual, code-mixed UPI SMS corpus.

Structure: TEMPLATES[label][subtype][lang] -> list of template strings.

Labels
  scam  : fraudulent / social-engineering messages (the positive class for FNR)
  legit : genuine transaction alerts, OTPs, advisories and personal payment chats
  promo : genuine commercial promotions (cashback, sales, loan offers, recharge)

Language pairs (romanised / transliterated, as typed on Indian phones)
  en : Indian English
  hi : Hindi-English  (Hinglish)
  ta : Tamil-English  (Tanglish)
  bn : Bengali-English (Benglish)
  te : Telugu-English (Tenglish)

Templates are deliberately *parallel* across languages (same intent, same slots)
so cross-lingual transfer can be studied under controlled conditions, and they
include hard negatives: genuine advisories that mention KYC/PIN/OTP, genuine
reward-point reminders, genuine loan promos and genuine "I sent you money"
chats, which mirror the vocabulary of scams.

Slots: {amt} {amt2} {bank} {app} {upi} {acct} {link} {phone} {otp} {date}
       {ref} {name} {merchant} {company} {company2} {job_amt} {prize}
       {courier} {days} {pct} {rate} {bank_helpline}
"""

TEMPLATES = {
    # ------------------------------------------------------------------ SCAM
    "scam": {
        "kyc_block": {
            "en": [
                "Dear customer your {bank} account will be blocked today at 12 midnight. Update your KYC immediately by clicking {link}",
                "{bank} ALERT: Your PAN is not linked, your account will be suspended. Update now: {link}",
                "Your KYC has expired. To avoid {app} wallet closure call {phone} immediately",
            ],
            "hi": [
                "Dear customer aapka {bank} account aaj raat 12 baje block ho jayega. KYC update karne ke liye turant is link pe click karein {link}",
                "{bank} ALERT: Aapka PAN card link nahi hai, account suspend kar diya jayega. Abhi update karein: {link}",
                "Priy grahak, aapki KYC expire ho gayi hai. {app} wallet band hone se bachane ke liye call karein {phone}",
            ],
            "ta": [
                "Dear customer, ungal {bank} account inniku night block aagidum. KYC update panna udane intha link-a click pannunga {link}",
                "{bank} ALERT: ungal PAN card link aagala, account suspend pannuvom. Ippove update pannunga {link}",
                "Ungaloda KYC expire aagiduchu. {app} wallet close aagama irukka {phone} ku call pannunga",
            ],
            "bn": [
                "Dear customer, apnar {bank} account aaj raat 12 tay block hoye jabe. KYC update korte ekhuni ei link e click korun {link}",
                "{bank} ALERT: apnar PAN card link nei, account suspend kora hobe. Ekhuni update korun {link}",
                "Apnar KYC expire hoye geche. {app} wallet bondho howa theke bachate {phone} e call korun",
            ],
            "te": [
                "Dear customer, mee {bank} account ee roju raatri 12 ki block avutundi. KYC update cheyyadaniki ippude ee link click cheyandi {link}",
                "{bank} ALERT: mee PAN card link avvaledu, account suspend chestamu. Ippude update cheyandi {link}",
                "Mee KYC expire ayyindi. {app} wallet close avvakunda {phone} ki call cheyandi",
            ],
        },
        "refund_collect": {
            "en": [
                "Congratulations! You have received {amt} cashback. To receive the money accept the request on {app} and enter your UPI PIN",
                "Your refund of {amt} is pending. Approve the collect request and enter PIN to claim. Ref {ref}",
                "{merchant} refund of {amt} is on its way to your account, just enter PIN on the request from {upi}",
            ],
            "hi": [
                "Congratulations! Aapko {amt} ka cashback mila hai. Paise receive karne ke liye {app} pe aaye request ko accept karke UPI PIN daalein",
                "Aapka refund {amt} pending hai. Amount claim karne ke liye collect request approve karein aur PIN enter karein. Ref {ref}",
                "{merchant} refund: {amt} aapke account me aane wala hai, bas {upi} se aayi request pe PIN daal do",
            ],
            "ta": [
                "Congratulations! Ungalukku {amt} cashback kidaichirukku. Panam receive panna {app}-la vandha request-a accept panni UPI PIN podunga",
                "Ungal refund {amt} pending-la irukku. Claim panna collect request approve panni PIN enter pannunga. Ref {ref}",
                "{merchant} refund {amt} ungal account-ku varudhu, {upi} kitta irundhu vandha request-la PIN pottaa podhum",
            ],
            "bn": [
                "Congratulations! Apni {amt} cashback peyechen. Taka receive korte {app} e asha request accept kore UPI PIN din",
                "Apnar refund {amt} pending ache. Claim korte collect request approve kore PIN enter korun. Ref {ref}",
                "{merchant} refund {amt} apnar account e ashche, shudhu {upi} theke asha request e PIN din",
            ],
            "te": [
                "Congratulations! Meeku {amt} cashback vachindi. Dabbulu receive cheyyadaniki {app} lo vachina request accept chesi UPI PIN enter cheyandi",
                "Mee refund {amt} pending lo undi. Claim cheyyadaniki collect request approve chesi PIN enter cheyandi. Ref {ref}",
                "{merchant} refund {amt} mee account ki vastundi, {upi} nunchi vachina request lo PIN veste chaalu",
            ],
        },
        "lottery_prize": {
            "en": [
                "Congrats! Your number has been selected in KBC lucky draw, prize {prize}. Send registration fee {amt} to {upi}",
                "You have won {prize} in the {app} mega contest! Fill your details at {link} to claim, offer valid only {days} days",
                "Airtel lucky winner: your number has won {prize}. WhatsApp {phone} now",
            ],
            "hi": [
                "Badhai ho! KBC lucky draw me aapka number select hua hai, inaam {prize}. Registration fee {amt} {upi} pe bhejein",
                "Aapne {app} mega contest me {prize} jeeta hai! Claim karne ke liye {link} pe details bharein, offer sirf {days} din ka hai",
                "Jio lucky winner: aapke number ne {prize} jeeta hai. WhatsApp karein {phone} turant",
            ],
            "ta": [
                "Vaazhthukkal! Lucky draw-la ungal number select aagirukku, parisu {prize}. Registration fee {amt} {upi} ku anuppunga",
                "Neenga {app} mega contest-la {prize} jeyichirukeenga! Claim panna {link}-la details fill pannunga, offer {days} naal mattum",
                "Airtel lucky winner: ungal number {prize} win pannirukku. Udane WhatsApp pannunga {phone}",
            ],
            "bn": [
                "Obhinandan! Lucky draw te apnar number select hoyeche, puroskar {prize}. Registration fee {amt} {upi} te pathan",
                "Apni {app} mega contest e {prize} jitechen! Claim korte {link} e details din, offer shudhu {days} din",
                "Vi lucky winner: apnar number {prize} jiteche. Ekhuni WhatsApp korun {phone}",
            ],
            "te": [
                "Abhinandanalu! Lucky draw lo mee number select ayyindi, bahumati {prize}. Registration fee {amt} {upi} ki pampandi",
                "Meeru {app} mega contest lo {prize} gelicharu! Claim cheyyadaniki {link} lo details fill cheyandi, offer {days} rojulu matrame",
                "Jio lucky winner: mee number {prize} gelichindi. Ippude WhatsApp cheyandi {phone}",
            ],
        },
        "wrong_transfer": {
            "en": [
                "Bro I transferred {amt} to your account by mistake, please send it back to {upi}, very urgent",
                "Sir I sent {amt} to the wrong number, see screenshot. Kindly return it to {upi}",
                "Hello my {amt} went to you by mistake, return it or I will file a police complaint {phone}",
            ],
            "hi": [
                "Bhai galti se aapke account me {amt} transfer ho gaye, please wapas {upi} pe bhej do, bahut zaroori hai",
                "Sir maine galat number pe {amt} bhej diya, screenshot dekh lo. Kripya {upi} pe return kar dijiye",
                "Hello mere {amt} galti se aapko chale gaye hai, plz return kardo warna police complaint karunga {phone}",
            ],
            "ta": [
                "Anna thappa ungal account-ku {amt} anuppiten, please thirumba {upi} ku anuppunga, romba urgent",
                "Sir naan wrong number-ku {amt} anuppiten, screenshot paarunga. Dayavu senju {upi} ku return pannunga",
                "Hello en {amt} thappa ungalukku poiduchu, return pannunga illana police complaint kudupen {phone}",
            ],
            "bn": [
                "Dada bhul kore apnar account e {amt} pathiye diyechi, please {upi} te ferot pathan, khub urgent",
                "Sir ami bhul number e {amt} pathiyechi, screenshot dekhun. Doya kore {upi} te return korun",
                "Hello amar {amt} bhul kore apnar kache chole geche, return korun noile police complaint korbo {phone}",
            ],
            "te": [
                "Anna porapatuna mee account ki {amt} pampanu, please {upi} ki tirigi pampandi, chala urgent",
                "Sir nenu wrong number ki {amt} pampanu, screenshot chudandi. Dayachesi {upi} ki return cheyandi",
                "Hello naa {amt} porapatuna meeku vellipoyindi, return cheyandi lekapothe police complaint istanu {phone}",
            ],
        },
        "job_task": {
            "en": [
                "Part time job! Earn {job_amt} daily from home, just like YouTube videos. WhatsApp {phone}",
                "Amazon work from home: daily income {job_amt}, joining fee only {amt}. Register now {link}",
                "Hello I am from HR, your resume has been shortlisted. Complete simple tasks and earn {job_amt}, join Telegram {link}",
            ],
            "hi": [
                "Part time job! Ghar baithe roz {job_amt} kamayein, sirf YouTube videos like karna hai. Contact WhatsApp {phone}",
                "Amazon work from home: daily {job_amt} income, joining fee sirf {amt}. Abhi register karein {link}",
                "Hello main HR se baat kar rahi hu, aapka resume select hua hai. Task complete karke {job_amt} paayein, Telegram join karein {link}",
            ],
            "ta": [
                "Part time job! Veetla irundhe dhinamum {job_amt} sambaathikalaam, YouTube video like pannaa podhum. WhatsApp {phone}",
                "Amazon work from home: daily {job_amt} income, joining fee {amt} mattum. Ippove register pannunga {link}",
                "Hello naan HR-la irundhu pesuren, ungal resume select aagirukku. Task mudichu {job_amt} vaangunga, Telegram join pannunga {link}",
            ],
            "bn": [
                "Part time job! Barite boshe roj {job_amt} income korun, shudhu YouTube video like korte hobe. WhatsApp {phone}",
                "Amazon work from home: daily {job_amt} income, joining fee matro {amt}. Ekhuni register korun {link}",
                "Hello ami HR theke bolchi, apnar resume select hoyeche. Task shesh kore {job_amt} pan, Telegram join korun {link}",
            ],
            "te": [
                "Part time job! Intlo nunche roju {job_amt} sampadinchandi, YouTube videos like cheste chaalu. WhatsApp {phone}",
                "Amazon work from home: daily {job_amt} income, joining fee {amt} matrame. Ippude register cheyandi {link}",
                "Hello nenu HR nunchi matladutunnanu, mee resume select ayyindi. Task purthi chesi {job_amt} pondandi, Telegram join avvandi {link}",
            ],
        },
        "bill_disconnect": {
            "en": [
                "Dear consumer your {company} electricity connection will be disconnected tonight at 9:30 as previous bill was not updated. Call {phone} immediately",
                "{company}: Your bill is pending and connection will be disconnected. Pay {amt} now {link}",
                "Dear consumer your power will be cut tonight. Contact electricity officer {phone}",
            ],
            "hi": [
                "Priy upbhokta aapka {company} bijli connection aaj raat 9:30 baje kat jayega kyunki pichla bill update nahi hua. Turant call karein {phone}",
                "{company}: Aapka bill pending hai, connection disconnect hoga. Abhi {amt} pay karein {link}",
                "Dear consumer aaj raat aapki light kat jayegi. Electricity officer se sampark karein {phone}",
            ],
            "ta": [
                "Anbulla nugarvor, ungal {company} current connection inniku raathiri 9:30 ku cut aagum, last bill update aagala. Udane call pannunga {phone}",
                "{company}: ungal bill pending, connection disconnect aagum. Ippove {amt} pay pannunga {link}",
                "Dear consumer inniku night ungal veetla current cut aagum. Electricity officer-a contact pannunga {phone}",
            ],
            "bn": [
                "Priyo grahok, apnar {company} electric connection aaj raat 9:30 e kete deoa hobe karon ager bill update hoyni. Ekhuni call korun {phone}",
                "{company}: apnar bill pending, connection disconnect hobe. Ekhuni {amt} pay korun {link}",
                "Dear consumer aaj raate apnar current kete jabe. Electricity officer er sathe jogajog korun {phone}",
            ],
            "te": [
                "Priyamaina viniyogadarudu, mee {company} current connection ee raatri 9:30 ki cut avutundi, last bill update avvaledu. Ippude call cheyandi {phone}",
                "{company}: mee bill pending undi, connection disconnect avutundi. Ippude {amt} pay cheyandi {link}",
                "Dear consumer ee raatri mee intlo current cut avutundi. Electricity officer ni sampradinchandi {phone}",
            ],
        },
        "parcel_customs": {
            "en": [
                "{courier}: Your parcel is held at customs. Pay {amt} release fee at {link}",
                "Your package could not be delivered due to incorrect address. Update address within 24 hours {link}",
                "A parcel in your name containing illegal items has been seized at the airport. Call {phone} immediately or an FIR will be filed",
            ],
            "hi": [
                "{courier}: Aapka parcel customs me ruka hai. Release ke liye {amt} fee bharein {link}",
                "Aapka package address galat hone ke karan deliver nahi hua. 24 ghante me address update karein {link}",
                "Aapke naam ka parcel airport pe pakda gaya hai jisme illegal saman hai. Turant {phone} pe call karein warna FIR hogi",
            ],
            "ta": [
                "{courier}: ungal parcel customs-la nikkudhu. Release panna {amt} fee kattunga {link}",
                "Thappana address-naala ungal package deliver aagala. 24 mani nerathula address update pannunga {link}",
                "Ungal per-la vandha parcel airport-la pidichirukkaanga, adhula illegal porul irukku. Udane {phone} ku call pannunga illana FIR podapadum",
            ],
            "bn": [
                "{courier}: apnar parcel customs e atke ache. Release er jonno {amt} fee din {link}",
                "Bhul address er jonno apnar package deliver hoyni. 24 ghontar moddhe address update korun {link}",
                "Apnar naame asha parcel airport e dhora poreche, tate illegal jinish ache. Ekhuni {phone} e call korun noile FIR hobe",
            ],
            "te": [
                "{courier}: mee parcel customs lo aagipoyindi. Release kosam {amt} fee kattandi {link}",
                "Tappu address valla mee package deliver avvaledu. 24 gantallo address update cheyandi {link}",
                "Mee peru meeda vachina parcel airport lo pattukunnaru, andulo illegal vastuvulu unnayi. Ippude {phone} ki call cheyandi lekapothe FIR avutundi",
            ],
        },
        "fake_support": {
            "en": [
                "{app} customer care: your transaction failed, to get refund download AnyDesk app and call {phone}",
                "Suspicious transaction of {amt} on your {bank} credit card. To cancel share the OTP, call {phone}",
                "We are calling from {bank} head office, your debit card is blocked, reply with card number and CVV to unblock",
            ],
            "hi": [
                "{app} customer care: aapka transaction fail hua hai, paise wapas lene ke liye AnyDesk app download karke {phone} pe call karein",
                "Aapke {bank} credit card pe {amt} ka suspicious transaction hua hai. Cancel karne ke liye OTP batayein, call {phone}",
                "Hum {bank} head office se bol rahe hai, aapka debit card block ho gaya hai, unblock ke liye card number aur CVV reply karein",
            ],
            "ta": [
                "{app} customer care: ungal transaction fail aagiduchu, panam thirumba vaanga AnyDesk app download panni {phone} ku call pannunga",
                "Ungal {bank} credit card-la {amt} suspicious transaction nadandhirukku. Cancel panna OTP sollunga, call {phone}",
                "Naanga {bank} head office-la irundhu pesurom, ungal debit card block aagiduchu, unblock panna card number, CVV reply pannunga",
            ],
            "bn": [
                "{app} customer care: apnar transaction fail hoyeche, taka ferot pete AnyDesk app download kore {phone} e call korun",
                "Apnar {bank} credit card e {amt} er suspicious transaction hoyeche. Cancel korte OTP bolun, call {phone}",
                "Amra {bank} head office theke bolchi, apnar debit card block hoye geche, unblock korte card number ar CVV reply korun",
            ],
            "te": [
                "{app} customer care: mee transaction fail ayyindi, dabbulu tirigi pondadaniki AnyDesk app download chesi {phone} ki call cheyandi",
                "Mee {bank} credit card lo {amt} suspicious transaction jarigindi. Cancel cheyyadaniki OTP cheppandi, call {phone}",
                "Memu {bank} head office nunchi matladutunnamu, mee debit card block ayyindi, unblock kosam card number, CVV reply cheyandi",
            ],
        },
        "loan_instant": {
            "en": [
                "Instant loan {amt} without CIBIL! Approval in 5 minutes with just Aadhaar and PAN. Send processing fee {amt2} to {upi}",
                "Pre approved loan of {amt} is ready for you. Download app now {link}, no documents needed",
                "Your loan is sanctioned. Pay file charge {amt2} and money will be credited instantly {phone}",
            ],
            "hi": [
                "Bina CIBIL ke instant loan {amt}! Sirf Aadhaar aur PAN se 5 minute me approval. Processing fee {amt2} bhejein {upi}",
                "Pre approved loan {amt} aapke liye ready hai. Abhi app download karein {link}, koi document nahi chahiye",
                "Aapka loan sanction ho gaya hai. File charge {amt2} pay karein aur paisa turant account me aayega {phone}",
            ],
            "ta": [
                "CIBIL illama instant loan {amt}! Aadhaar PAN mattum podhum, 5 nimishathula approval. Processing fee {amt2} {upi} ku anuppunga",
                "Pre approved loan {amt} ungalukku ready. Ippove app download pannunga {link}, endha document-um vendaam",
                "Ungal loan sanction aagiduchu. File charge {amt2} pay pannunga, panam udane account-ku varum {phone}",
            ],
            "bn": [
                "CIBIL chara instant loan {amt}! Shudhu Aadhaar ar PAN diye 5 minute e approval. Processing fee {amt2} {upi} te pathan",
                "Pre approved loan {amt} apnar jonno ready. Ekhuni app download korun {link}, kono document lagbe na",
                "Apnar loan sanction hoye geche. File charge {amt2} pay korun, taka sathe sathe account e ashbe {phone}",
            ],
            "te": [
                "CIBIL lekunda instant loan {amt}! Aadhaar, PAN tho 5 nimishallo approval. Processing fee {amt2} {upi} ki pampandi",
                "Pre approved loan {amt} meekosam ready. Ippude app download cheyandi {link}, e document avasaram ledu",
                "Mee loan sanction ayyindi. File charge {amt2} pay cheyandi, dabbulu ventane account ki vastayi {phone}",
            ],
        },
        "reward_phish": {
            "en": [
                "Your {bank} reward points worth {amt} expire today, redeem now {link}",
                "{bank} credit card points are about to expire! Convert {amt} to cash, click {link}",
                "Your {app} reward of {amt} is unclaimed, today is the last day. Claim at {link}",
            ],
            "hi": [
                "Aapke {bank} reward points jinki value {amt} hai aaj expire ho rahe hai, abhi redeem karein {link}",
                "{bank} credit card points expire hone wale hai! {amt} cash me badalne ke liye {link} pe click karein",
                "Aapka {app} reward {amt} abhi tak claim nahi hua, aaj aakhri din hai. Claim karein {link}",
            ],
            "ta": [
                "Ungal {bank} reward points {amt} mathippu inniku expire aagudhu, ippove redeem pannunga {link}",
                "{bank} credit card points expire aaga poguthu! {amt} cash-a maatha {link} click pannunga",
                "Ungal {app} reward {amt} claim pannala, inniku last day. Claim panna {link}",
            ],
            "bn": [
                "Apnar {bank} reward points jar mullo {amt} aaj expire hocche, ekhuni redeem korun {link}",
                "{bank} credit card points expire hote choleche! {amt} cash e convert korte {link} e click korun",
                "Apnar {app} reward {amt} ekhono claim korenni, aaj shesh din. Claim korun {link}",
            ],
            "te": [
                "Mee {bank} reward points viluva {amt} ee roju expire avutunnayi, ippude redeem cheyandi {link}",
                "{bank} credit card points expire avvabotunnayi! {amt} cash ga marchukovadaniki {link} click cheyandi",
                "Mee {app} reward {amt} inka claim cheyyaledu, ee roju last day. Claim cheyandi {link}",
            ],
        },
    },
    # ----------------------------------------------------------------- LEGIT
    "legit": {
        "debit_alert": {
            "en": [
                "{amt} debited from A/c {acct} on {date} to VPA {upi}. UPI Ref No {ref}. Not you? Call {bank_helpline} -{bank}",
                "{bank}: A/c {acct} debited by {amt} for {merchant}. Avl Bal {amt2}. Ref {ref}",
                "You paid {amt} to {name} via {app}. UPI Ref {ref}. Thank you",
            ],
            "hi": [
                "Aapke A/c {acct} se {date} ko {amt} debit hue, {upi} ko UPI ke through. Ref {ref}. Agar aapne nahi kiya to {bank_helpline} pe call karein -{bank}",
                "{bank}: A/c {acct} me se {amt} {merchant} ko bheje gaye. Upalabdh balance {amt2}. Ref {ref}",
                "Aapne {app} se {name} ko {amt} bheje. UPI Ref {ref}. Dhanyavaad",
            ],
            "ta": [
                "Ungal A/c {acct}-la irundhu {date} anru {amt} debit aagirukku, {upi} ku UPI moolam. Ref {ref}. Neenga illaina {bank_helpline} ku call pannunga -{bank}",
                "{bank}: A/c {acct}-la irundhu {amt} {merchant} ku anuppapattadhu. Balance {amt2}. Ref {ref}",
                "Neenga {app} moolama {name} ku {amt} anuppineenga. UPI Ref {ref}. Nandri",
            ],
            "bn": [
                "Apnar A/c {acct} theke {date} e {amt} debit hoyeche, {upi} ke UPI diye. Ref {ref}. Apni na korle {bank_helpline} e call korun -{bank}",
                "{bank}: A/c {acct} theke {amt} {merchant} ke pathano hoyeche. Balance {amt2}. Ref {ref}",
                "Apni {app} diye {name} ke {amt} pathiyechen. UPI Ref {ref}. Dhonnobad",
            ],
            "te": [
                "Mee A/c {acct} nunchi {date} na {amt} debit ayyindi, {upi} ki UPI dwara. Ref {ref}. Meeru kakapothe {bank_helpline} ki call cheyandi -{bank}",
                "{bank}: A/c {acct} nunchi {amt} {merchant} ki pampabadindi. Balance {amt2}. Ref {ref}",
                "Meeru {app} dwara {name} ki {amt} pamparu. UPI Ref {ref}. Dhanyavadalu",
            ],
        },
        "credit_alert": {
            "en": [
                "Your A/c {acct} is credited with {amt} on {date} from {name} ({upi}). UPI Ref {ref} -{bank}",
                "{amt} has been added to your {app} wallet. Transaction ID {ref}",
                "Salary credit: {amt} credited to your {bank} A/c {acct}. Use {bank} app to check balance",
            ],
            "hi": [
                "Aapke A/c {acct} me {amt} credit hue {date} ko, {name} ({upi}) se. UPI Ref {ref} -{bank}",
                "{amt} aapke {app} wallet me jama ho gaye hai. Transaction ID {ref}",
                "Salary credit: {amt} aapke {bank} A/c {acct} me jama kiya gaya. Balance check ke liye {bank} app use karein",
            ],
            "ta": [
                "Ungal A/c {acct}-la {date} anru {amt} credit aagirukku, {name} ({upi}) kitta irundhu. UPI Ref {ref} -{bank}",
                "{amt} ungal {app} wallet-la add aagiduchu. Transaction ID {ref}",
                "Salary credit: {amt} ungal {bank} A/c {acct}-la pottachu. Balance paarkka {bank} app use pannunga",
            ],
            "bn": [
                "Apnar A/c {acct} e {date} e {amt} credit hoyeche, {name} ({upi}) theke. UPI Ref {ref} -{bank}",
                "{amt} apnar {app} wallet e joma hoyeche. Transaction ID {ref}",
                "Salary credit: {amt} apnar {bank} A/c {acct} e joma kora hoyeche. Balance dekhte {bank} app use korun",
            ],
            "te": [
                "Mee A/c {acct} lo {date} na {amt} credit ayyindi, {name} ({upi}) nunchi. UPI Ref {ref} -{bank}",
                "{amt} mee {app} wallet lo jama ayyindi. Transaction ID {ref}",
                "Salary credit: {amt} mee {bank} A/c {acct} lo jama cheyabadindi. Balance chudataniki {bank} app vadandi",
            ],
        },
        "otp": {
            "en": [
                "{otp} is your {bank} OTP for transaction of {amt}. Do not share this OTP with anyone. Bank never asks for OTP",
                "{app} login OTP: {otp}. Valid for 10 mins. Do not share, {app} never calls asking for OTP",
                "Your UPI PIN reset OTP is {otp}. If not requested by you contact {bank_helpline} immediately",
            ],
            "hi": [
                "{otp} aapka {bank} OTP hai {amt} ke transaction ke liye. Yeh OTP kisi ke saath share na karein. Bank kabhi OTP nahi maangta",
                "{app} login OTP: {otp}. Valid 10 min. Kisi ko bhi na batayein, {app} kabhi call karke OTP nahi poochta",
                "Aapka UPI PIN reset OTP {otp} hai. Agar aapne request nahi ki to turant {bank_helpline} pe sampark karein",
            ],
            "ta": [
                "{otp} ungal {bank} OTP, {amt} transaction-ku. Indha OTP-a yaar kittayum share pannadheenga. Bank eppovum OTP kekkadhu",
                "{app} login OTP: {otp}. 10 nimisham valid. Yaarukkum sollaadheenga, {app} call panni OTP kekkadhu",
                "Ungal UPI PIN reset OTP {otp}. Neenga request pannalaina udane {bank_helpline}-a contact pannunga",
            ],
            "bn": [
                "{otp} apnar {bank} OTP {amt} er transaction er jonno. Ei OTP karo sathe share korben na. Bank kokhono OTP chay na",
                "{app} login OTP: {otp}. 10 minute valid. Kauke bolben na, {app} kokhono call kore OTP chay na",
                "Apnar UPI PIN reset OTP {otp}. Apni request na korle ekhuni {bank_helpline} e jogajog korun",
            ],
            "te": [
                "{otp} mee {bank} OTP {amt} transaction kosam. Ee OTP evaritho share cheyakandi. Bank eppudu OTP adagadu",
                "{app} login OTP: {otp}. 10 nimishalu valid. Evariki cheppakandi, {app} call chesi OTP adagadu",
                "Mee UPI PIN reset OTP {otp}. Meeru request cheyyakapothe ventane {bank_helpline} ni sampradinchandi",
            ],
        },
        "collect_genuine": {
            "en": [
                "{merchant} has sent you a payment request of {amt} on {app}. Approve in app if you placed the order, else decline",
                "{name} has requested {amt} on {app}. Remember, you never need to enter PIN to RECEIVE money",
                "Payment request: {company} bill {amt}, due date {date}. Pay via {app} app",
            ],
            "hi": [
                "{merchant} ne aapko {app} pe {amt} ki payment request bheji hai. Agar aapne order kiya hai to app me approve karein, warna decline karein",
                "{name} ne {amt} ki request bheji hai {app} pe. Yaad rakhein, paise RECEIVE karne ke liye PIN kabhi nahi daalna padta",
                "Payment request: {company} bill {amt}, due date {date}. {app} app me jaake pay karein",
            ],
            "ta": [
                "{merchant} ungalukku {app}-la {amt} payment request anuppirukku. Neenga order pannirundhaa app-la approve pannunga, illana decline pannunga",
                "{name} {amt} request anuppirukaanga {app}-la. Nyaabagam vechikonga, panam RECEIVE panna PIN theva illa",
                "Payment request: {company} bill {amt}, kadaisi thedhi {date}. {app} app-la pay pannunga",
            ],
            "bn": [
                "{merchant} apnake {app} e {amt} er payment request pathiyeche. Apni order kore thakle app e approve korun, noile decline korun",
                "{name} {amt} er request pathiyeche {app} e. Mone rakhben, taka RECEIVE korte kokhono PIN lage na",
                "Payment request: {company} bill {amt}, shesh tarikh {date}. {app} app e giye pay korun",
            ],
            "te": [
                "{merchant} meeku {app} lo {amt} payment request pampindi. Meeru order chesi unte app lo approve cheyandi, lekapothe decline cheyandi",
                "{name} {amt} request pamparu {app} lo. Gurtunchukondi, dabbulu RECEIVE cheyyadaniki PIN avasaram ledu",
                "Payment request: {company} bill {amt}, chivari tedi {date}. {app} app lo pay cheyandi",
            ],
        },
        "personal": {
            "en": [
                "Hey send the {amt} for yesterday's dinner to {upi} whenever free",
                "Mom sent {amt} on GPay, check once",
                "Hi {name}, I have transferred {amt}, sending screenshot. Ref {ref}",
                "Will send this month's rent {amt} a bit late, by {date} for sure",
            ],
            "hi": [
                "Bhai kal ke dinner ka {amt} {upi} pe bhej dena jab time mile",
                "Mummy ne {amt} GPay pe bhej diye hai, check kar lena",
                "Arre {name}, maine {amt} transfer kar diya, screenshot bhej raha hu. Ref {ref}",
                "Rent ke {amt} is mahine thoda late bhejunga yaar, {date} tak pakka",
            ],
            "ta": [
                "Machan nethu dinner {amt} {upi} ku anuppidu time irukkumbodhu",
                "Amma {amt} GPay-la anuppirukaanga, check pannu",
                "Dei {name}, naan {amt} transfer panniten, screenshot anupuren. Ref {ref}",
                "Rent {amt} indha maasam konjam late-a anupuren da, {date} kulla kandippa",
            ],
            "bn": [
                "Bhai kaler dinner er {amt} {upi} te pathiye dis somoy pele",
                "Ma {amt} GPay te pathiyeche, check kore nis",
                "Are {name}, ami {amt} transfer kore diyechi, screenshot pathacchi. Ref {ref}",
                "Ei mash e rent er {amt} ektu deri te pathabo, {date} er moddhe pakka",
            ],
            "te": [
                "Ra ninna dinner {amt} {upi} ki pampu time unnappudu",
                "Amma {amt} GPay lo pampindi, check cheyyi",
                "Orey {name}, nenu {amt} transfer chesanu, screenshot pamputunna. Ref {ref}",
                "Ee nela rent {amt} konchem late ga pamputanu ra, {date} lopu kachitanga",
            ],
        },
        "security_advisory": {
            "en": [
                "{bank} never asks for your PIN, OTP or CVV over call/SMS. For KYC update visit branch or use official app only",
                "Beware! UPI PIN is not required to receive money. Do not click unknown links -{bank}",
                "RBI says: report fraud calls at 1930. Update your KYC only at {bank} branch",
            ],
            "hi": [
                "{bank} kabhi bhi call/SMS se aapka PIN, OTP ya CVV nahi maangta. KYC update ke liye sirf branch jaayein ya official app use karein",
                "Saavdhan! Paise receive karne ke liye UPI PIN ki zaroorat nahi hoti. Kisi anjaan link pe click na karein -{bank}",
                "RBI kehta hai: fraud call aaye to 1930 pe report karein. Apna KYC sirf {bank} branch me update karein",
            ],
            "ta": [
                "{bank} eppovum call/SMS moolama ungal PIN, OTP, CVV kekkadhu. KYC update-ku branch-ku mattum ponga illa official app use pannunga",
                "Jaakiradhai! Panam receive panna UPI PIN theva illa. Theriyaadha link-a click pannadheenga -{bank}",
                "RBI: fraud call vandha 1930-la report pannunga. Ungal KYC-a {bank} branch-la mattum update pannunga",
            ],
            "bn": [
                "{bank} kokhono call/SMS e apnar PIN, OTP ba CVV chay na. KYC update er jonno shudhu branch e jan ba official app use korun",
                "Sabdhan! Taka receive korte UPI PIN lage na. Ochena link e click korben na -{bank}",
                "RBI: fraud call ele 1930 e report korun. Apnar KYC shudhu {bank} branch e update korun",
            ],
            "te": [
                "{bank} eppudu call/SMS dwara mee PIN, OTP leda CVV adagadu. KYC update kosam branch ki matrame vellandi leda official app vadandi",
                "Jagratta! Dabbulu receive cheyyadaniki UPI PIN avasaram ledu. Teliyani link click cheyakandi -{bank}",
                "RBI: fraud call vaste 1930 lo report cheyandi. Mee KYC ni {bank} branch lo matrame update cheyandi",
            ],
        },
        "bill_paid": {
            "en": [
                "Your {company} bill of {amt} is paid successfully. Transaction ID {ref}. Thank you",
                "Payment of {amt} for your {merchant} order is successful. Order will be delivered by {date}",
                "Your {app} recharge of {amt} is successful. Validity {days} days. Ref {ref}",
            ],
            "hi": [
                "Aapka {company} bill {amt} successfully pay ho gaya. Transaction ID {ref}. Dhanyavaad",
                "{merchant} order ke liye {amt} ki payment safal rahi. Order {date} tak deliver hoga",
                "Aapka {app} recharge {amt} successful. Validity {days} din. Ref {ref}",
            ],
            "ta": [
                "Ungal {company} bill {amt} vetrigaramaga pay aagiduchu. Transaction ID {ref}. Nandri",
                "{merchant} order-ku {amt} payment success. Order {date} kulla deliver aagum",
                "Ungal {app} recharge {amt} success. Validity {days} naal. Ref {ref}",
            ],
            "bn": [
                "Apnar {company} bill {amt} successfully pay hoyeche. Transaction ID {ref}. Dhonnobad",
                "{merchant} order er jonno {amt} payment safol hoyeche. Order {date} er moddhe deliver hobe",
                "Apnar {app} recharge {amt} successful. Validity {days} din. Ref {ref}",
            ],
            "te": [
                "Mee {company} bill {amt} vijayavantanga pay ayyindi. Transaction ID {ref}. Dhanyavadalu",
                "{merchant} order kosam {amt} payment success. Order {date} lopu deliver avutundi",
                "Mee {app} recharge {amt} successful. Validity {days} rojulu. Ref {ref}",
            ],
        },
    },
    # ----------------------------------------------------------------- PROMO
    "promo": {
        "cashback_offer": {
            "en": [
                "Pay at {merchant} via {app} and get {pct}% cashback up to {amt}. Offer till {date}. T&C apply",
                "Today only! Pay bills on {app} and win cashback up to {amt}. Open now {link}",
                "Super offer: flat {amt} cashback on UPI payments at {merchant}. *T&C",
            ],
            "hi": [
                "{app} pe {merchant} se payment karein aur payein {pct}% cashback, max {amt}. Offer {date} tak. T&C apply",
                "Sirf aaj! {app} se bill pay karo aur jeeto {amt} tak cashback. Abhi kholo {link}",
                "Dhamaka offer: {merchant} pe UPI se pay karne par flat {amt} cashback. *T&C",
            ],
            "ta": [
                "{app}-la {merchant} payment pannunga, {pct}% cashback perunga, max {amt}. Offer {date} varai. T&C apply",
                "Inniku mattum! {app}-la bill pay panni {amt} varai cashback jeyinga. Ippove open pannunga {link}",
                "Super offer: {merchant}-la UPI-la pay panna flat {amt} cashback. *T&C",
            ],
            "bn": [
                "{app} e {merchant} payment korun ar pan {pct}% cashback, max {amt}. Offer {date} porjonto. T&C apply",
                "Shudhu aaj! {app} diye bill pay kore jitun {amt} porjonto cashback. Ekhuni khulun {link}",
                "Darun offer: {merchant} e UPI diye pay korle flat {amt} cashback. *T&C",
            ],
            "te": [
                "{app} lo {merchant} payment cheyandi, {pct}% cashback pondandi, max {amt}. Offer {date} varaku. T&C apply",
                "Ee roju matrame! {app} lo bill pay chesi {amt} varaku cashback gelavandi. Ippude open cheyandi {link}",
                "Super offer: {merchant} lo UPI tho pay cheste flat {amt} cashback. *T&C",
            ],
        },
        "sale_offer": {
            "en": [
                "{merchant} Festive sale is live! Up to {pct}% off on all products. Shop now {link}",
                "Big sale alert! {pct}% off on electronics at {merchant} for {days} days only. T&C",
                "Flat {pct}% off on new collection, visit {merchant} store or order at {link}",
            ],
            "hi": [
                "{merchant} Diwali sale shuru! Har product pe {pct}% tak off. Shop now {link}",
                "Big sale alert! {merchant} pe electronics pe {pct}% off sirf {days} din ke liye. T&C",
                "Naye collection pe flat {pct}% chhoot, {merchant} store pe aayein ya order karein {link}",
            ],
            "ta": [
                "{merchant} Deepavali sale aarambam! Ella product-kum {pct}% varai off. Shop now {link}",
                "Big sale alert! {merchant}-la electronics-ku {pct}% off {days} naal mattum. T&C",
                "Pudhu collection-ku flat {pct}% thallupadi, {merchant} store-ku vaanga illa order pannunga {link}",
            ],
            "bn": [
                "{merchant} Pujo sale shuru! Sob product e {pct}% porjonto chhar. Shop now {link}",
                "Big sale alert! {merchant} e electronics e {pct}% off shudhu {days} din. T&C",
                "Notun collection e flat {pct}% chhar, {merchant} store e ashun ba order korun {link}",
            ],
            "te": [
                "{merchant} Dasara sale modalaindi! Anni products pai {pct}% varaku off. Shop now {link}",
                "Big sale alert! {merchant} lo electronics pai {pct}% off {days} rojulu matrame. T&C",
                "Kotha collection pai flat {pct}% discount, {merchant} store ki randi leda order cheyandi {link}",
            ],
        },
        "loan_promo": {
            "en": [
                "{bank}: Pre-approved personal loan up to {amt} at attractive rates. Apply on {bank} app. T&C apply",
                "{bank} Gold loan now at just {rate}% interest. Visit nearest branch",
                "Fulfil your dream home with {bank} home loan. Low EMI, quick approval. {link}",
            ],
            "hi": [
                "{bank}: Aapke liye pre-approved personal loan {amt} tak, attractive interest rate. Apply karein {bank} app pe. T&C apply",
                "{bank} Gold loan ab sirf {rate}% byaj par. Najdeeki branch me sampark karein",
                "Ghar ka sapna poora karein {bank} home loan ke saath. Kam EMI, jaldi approval. {link}",
            ],
            "ta": [
                "{bank}: ungalukku {amt} varai pre-approved personal loan, kuraindha vatti. {bank} app-la apply pannunga. T&C apply",
                "{bank} Gold loan ippo {rate}% vatti-la. Pakkathula irukkura branch-a contact pannunga",
                "Sondha veedu kanavu {bank} home loan-oda niraiverum. Kuraindha EMI, seekiram approval. {link}",
            ],
            "bn": [
                "{bank}: apnar jonno {amt} porjonto pre-approved personal loan, kom sud. {bank} app e apply korun. T&C apply",
                "{bank} Gold loan ekhon matro {rate}% sude. Kacher branch e jogajog korun",
                "Nijer barir swapno puron korun {bank} home loan diye. Kom EMI, druto approval. {link}",
            ],
            "te": [
                "{bank}: meeku {amt} varaku pre-approved personal loan, takkuva vaddi. {bank} app lo apply cheyandi. T&C apply",
                "{bank} Gold loan ippudu {rate}% vaddi ki. Daggaralo unna branch ni sampradinchandi",
                "Sontha illu kala {bank} home loan tho neraverchukondi. Takkuva EMI, twaraga approval. {link}",
            ],
        },
        "recharge_plan": {
            "en": [
                "{company2} new plan: {amt} for 2GB/day, unlimited calls, {days} days validity. Recharge on {app}",
                "Your {company2} plan expires in {days} days. Recharge now and enjoy unlimited data {link}",
                "Special offer: extra 10GB data free on {amt} recharge. Hurry!",
            ],
            "hi": [
                "{company2} ka naya plan: {amt} me 2GB/din, unlimited calls, {days} din validity. Recharge karein {app} pe",
                "Aapka {company2} plan {days} din me khatam ho raha hai. Recharge karke unlimited data ka maza lein {link}",
                "Special offer: {amt} ke recharge pe extra 10GB data free. Jaldi karein!",
            ],
            "ta": [
                "{company2} pudhu plan: {amt}-ku 2GB/naal, unlimited calls, {days} naal validity. {app}-la recharge pannunga",
                "Ungal {company2} plan {days} naal-la mudiyudhu. Recharge panni unlimited data enjoy pannunga {link}",
                "Special offer: {amt} recharge-ku extra 10GB data free. Seekiram!",
            ],
            "bn": [
                "{company2} er notun plan: {amt} e 2GB/din, unlimited calls, {days} din validity. {app} e recharge korun",
                "Apnar {company2} plan {days} din e shesh hocche. Recharge kore unlimited data upobhog korun {link}",
                "Special offer: {amt} recharge e extra 10GB data free. Taratari korun!",
            ],
            "te": [
                "{company2} kotha plan: {amt} ki 2GB/roju, unlimited calls, {days} rojula validity. {app} lo recharge cheyandi",
                "Mee {company2} plan {days} rojullo aipotundi. Recharge chesi unlimited data enjoy cheyandi {link}",
                "Special offer: {amt} recharge ki extra 10GB data free. Twaraga cheyandi!",
            ],
        },
        "rewards_points": {
            "en": [
                "Your {bank} credit card reward points will expire on {date}. Redeem them on {bank} app",
                "You won a {app} scratch card! Check rewards section in your {app} app",
                "You have coins worth {amt} in your {merchant} wallet, use them on your next purchase. Valid {days} days",
            ],
            "hi": [
                "Aapke {bank} credit card ke reward points {date} ko expire ho rahe hai. Inhe {bank} app me redeem karein",
                "{app} scratch card jeeta! Apne {app} app me rewards section check karein",
                "Aapke {merchant} wallet me {amt} ke coins hai, agli shopping me use karein. Valid {days} din",
            ],
            "ta": [
                "Ungal {bank} credit card reward points {date} anru expire aagum. {bank} app-la redeem pannunga",
                "{app} scratch card jeyichirukeenga! Ungal {app} app-la rewards section paarunga",
                "Ungal {merchant} wallet-la {amt} coins irukku, adutha shopping-la use pannunga. {days} naal valid",
            ],
            "bn": [
                "Apnar {bank} credit card er reward points {date} e expire hobe. {bank} app e redeem korun",
                "{app} scratch card jitechen! Apnar {app} app e rewards section dekhun",
                "Apnar {merchant} wallet e {amt} er coins ache, porer shopping e use korun. {days} din valid",
            ],
            "te": [
                "Mee {bank} credit card reward points {date} na expire avutayi. {bank} app lo redeem cheyandi",
                "{app} scratch card gelicharu! Mee {app} app lo rewards section chudandi",
                "Mee {merchant} wallet lo {amt} coins unnayi, next shopping lo vadandi. {days} rojulu valid",
            ],
        },
    },
}

LANGS = ["en", "hi", "ta", "bn", "te"]
LANG_NAMES = {
    "en": "English",
    "hi": "Hindi-English",
    "ta": "Tamil-English",
    "bn": "Bengali-English",
    "te": "Telugu-English",
}
LABELS = ["legit", "promo", "scam"]
