"""
Message templates for UPI-MixSMS, the multilingual code-mixed UPI SMS corpus.

TEMPLATES[label][subtype][lang] -> list of template strings.

Labels
  scam  : fraudulent / social-engineering messages (the positive class for FNR)
  legit : genuine transaction alerts, OTPs, mandates, advisories and personal payment chats
  promo : genuine commercial promotions (cashback, sales, loan offers, recharge)

Languages (the design is language-agnostic: adding a language means adding one parallel
template list per subtype and one script module; nothing else is language-specific)
  en : English
  hi : Hindi-English code-mixed text -- Hindi in Devanagari script (templates_hi.py)
  ta : Tamil-English code-mixed text -- Tamil in Tamil script
  In both code-mixed settings the English banking vocabulary (KYC, account, link, OTP,
  PIN, refund, app names ...) stays in Latin script, which is how people actually type
  payment messages. Romanised forms (Hinglish, Tanglish) are NOT language settings; they
  only appear as the transliteration attack at obfuscation level L4.

Templates are parallel across languages (same intent, same slots) and include hard
negatives: genuine advisories that mention KYC/PIN/OTP, genuine reward-point reminders,
genuine loan promos, genuine AutoPay mandates and genuine "I sent you money" chats,
which use the same vocabulary as scams.

Slots: {amt} {amt2} {bank} {app} {upi} {acct} {link} {phone} {otp} {date} {ref} {name}
       {merchant} {company} {company2} {job_amt} {prize} {courier} {days} {pct} {rate}
       {bank_helpline}
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
            "ta": [
                "அன்புள்ள வாடிக்கையாளரே, உங்கள் {bank} account இன்று இரவு 12 மணிக்கு block செய்யப்படும். உடனே KYC update செய்ய இந்த link-ஐ click செய்யவும் {link}",
                "{bank} ALERT: உங்கள் PAN card link செய்யப்படவில்லை, account suspend செய்யப்படும். இப்போதே update செய்யுங்கள் {link}",
                "உங்கள் KYC காலாவதியாகிவிட்டது. {app} wallet மூடப்படாமல் இருக்க உடனே {phone} எண்ணுக்கு call செய்யவும்",
            ],
        },
        "refund_collect": {
            "en": [
                "Congratulations! You have received {amt} cashback. To receive the money accept the request on {app} and enter your UPI PIN",
                "Your refund of {amt} is pending. Approve the collect request and enter PIN to claim. Ref {ref}",
                "{merchant} refund of {amt} is on its way to your account, just enter PIN on the request from {upi}",
            ],
            "ta": [
                "வாழ்த்துக்கள்! உங்களுக்கு {amt} cashback கிடைத்துள்ளது. பணத்தைப் பெற {app}-ல் வந்த request-ஐ accept செய்து UPI PIN உள்ளிடவும்",
                "உங்கள் {amt} refund நிலுவையில் உள்ளது. பெற collect request-ஐ approve செய்து PIN enter செய்யவும். Ref {ref}",
                "{merchant} refund {amt} உங்கள் account-க்கு வருகிறது, {upi} அனுப்பிய request-ல் PIN போட்டால் போதும்",
            ],
        },
        "lottery_prize": {
            "en": [
                "Congrats! Your number has been selected in KBC lucky draw, prize {prize}. Send registration fee {amt} to {upi}",
                "You have won {prize} in the {app} mega contest! Fill your details at {link} to claim, offer valid only {days} days",
                "Airtel lucky winner: your number has won {prize}. WhatsApp {phone} now",
            ],
            "ta": [
                "வாழ்த்துக்கள்! lucky draw-வில் உங்கள் எண் தேர்வாகியுள்ளது, பரிசு {prize}. Registration fee {amt}-ஐ {upi}-க்கு அனுப்பவும்",
                "{app} mega contest-ல் நீங்கள் {prize} வென்றுள்ளீர்கள்! பெற {link}-ல் விவரங்களை நிரப்புங்கள், offer {days} நாட்கள் மட்டுமே",
                "Airtel lucky winner: உங்கள் எண் {prize} வென்றுள்ளது. உடனே WhatsApp செய்யுங்கள் {phone}",
            ],
        },
        "wrong_transfer": {
            "en": [
                "Bro I transferred {amt} to your account by mistake, please send it back to {upi}, very urgent",
                "Sir I sent {amt} to the wrong number, see screenshot. Kindly return it to {upi}",
                "Hello my {amt} went to you by mistake, return it or I will file a police complaint {phone}",
            ],
            "ta": [
                "அண்ணா, தவறுதலாக உங்கள் account-க்கு {amt} transfer ஆகிவிட்டது, தயவுசெய்து {upi}-க்கு திருப்பி அனுப்புங்கள், ரொம்ப urgent",
                "Sir, நான் தவறான எண்ணுக்கு {amt} அனுப்பிவிட்டேன், screenshot பாருங்கள். தயவுசெய்து {upi}-க்கு return செய்யுங்கள்",
                "Hello, என் {amt} தவறுதலாக உங்களுக்கு வந்துவிட்டது, திருப்பி அனுப்பாவிட்டால் police complaint கொடுப்பேன் {phone}",
            ],
        },
        "job_task": {
            "en": [
                "Part time job! Earn {job_amt} daily from home, just like YouTube videos. WhatsApp {phone}",
                "Amazon work from home: daily income {job_amt}, joining fee only {amt}. Register now {link}",
                "Hello I am from HR, your resume has been shortlisted. Complete simple tasks and earn {job_amt}, join Telegram {link}",
            ],
            "ta": [
                "Part time job! வீட்டிலிருந்தே தினமும் {job_amt} சம்பாதிக்கலாம், YouTube video-க்களை like செய்தால் போதும். WhatsApp {phone}",
                "Amazon work from home: தினசரி வருமானம் {job_amt}, joining fee {amt} மட்டுமே. இப்போதே register செய்யுங்கள் {link}",
                "வணக்கம், நான் HR-லிருந்து பேசுகிறேன், உங்கள் resume shortlist ஆகியுள்ளது. சின்ன task-களை முடித்து {job_amt} பெறுங்கள், Telegram-ல் join செய்யுங்கள் {link}",
            ],
        },
        "bill_disconnect": {
            "en": [
                "Dear consumer your {company} electricity connection will be disconnected tonight at 9:30 as previous bill was not updated. Call {phone} immediately",
                "{company}: Your bill is pending and connection will be disconnected. Pay {amt} now {link}",
                "Dear consumer your power will be cut tonight. Contact electricity officer {phone}",
            ],
            "ta": [
                "அன்புள்ள நுகர்வோரே, முந்தைய bill update ஆகாததால் உங்கள் {company} மின் இணைப்பு இன்று இரவு 9:30-க்கு துண்டிக்கப்படும். உடனே {phone} எண்ணை அழைக்கவும்",
                "{company}: உங்கள் bill நிலுவையில் உள்ளது, connection துண்டிக்கப்படும். இப்போதே {amt} செலுத்துங்கள் {link}",
                "Dear consumer, இன்று இரவு உங்கள் வீட்டில் current cut செய்யப்படும். Electricity officer-ஐ தொடர்பு கொள்ளுங்கள் {phone}",
            ],
        },
        "parcel_customs": {
            "en": [
                "{courier}: Your parcel is held at customs. Pay {amt} release fee at {link}",
                "Your package could not be delivered due to incorrect address. Update address within 24 hours {link}",
                "A parcel in your name containing illegal items has been seized at the airport. Call {phone} immediately or an FIR will be filed",
            ],
            "ta": [
                "{courier}: உங்கள் parcel customs-ல் நிறுத்தி வைக்கப்பட்டுள்ளது. Release fee {amt} செலுத்துங்கள் {link}",
                "தவறான முகவரி காரணமாக உங்கள் package deliver செய்ய முடியவில்லை. 24 மணி நேரத்தில் address update செய்யுங்கள் {link}",
                "உங்கள் பெயரில் வந்த parcel-ல் சட்டவிரோத பொருட்கள் இருப்பதால் airport-ல் பறிமுதல் செய்யப்பட்டது. உடனே {phone} எண்ணை அழைக்கவும், இல்லையெனில் FIR பதிவு செய்யப்படும்",
            ],
        },
        "fake_support": {
            "en": [
                "{app} customer care: your transaction failed, to get refund download AnyDesk app and call {phone}",
                "Suspicious transaction of {amt} on your {bank} credit card. To cancel share the OTP, call {phone}",
                "We are calling from {bank} head office, your debit card is blocked, reply with card number and CVV to unblock",
            ],
            "ta": [
                "{app} customer care: உங்கள் transaction தோல்வியடைந்தது, refund பெற AnyDesk app-ஐ download செய்து {phone} எண்ணுக்கு call செய்யவும்",
                "உங்கள் {bank} credit card-ல் {amt} சந்தேகத்திற்குரிய transaction நடந்துள்ளது. Cancel செய்ய OTP-ஐ சொல்லுங்கள், call {phone}",
                "நாங்கள் {bank} head office-லிருந்து பேசுகிறோம், உங்கள் debit card block ஆகிவிட்டது, unblock செய்ய card number மற்றும் CVV-ஐ reply செய்யவும்",
            ],
        },
        "loan_instant": {
            "en": [
                "Instant loan {amt} without CIBIL! Approval in 5 minutes with just Aadhaar and PAN. Send processing fee {amt2} to {upi}",
                "Pre approved loan of {amt} is ready for you. Download app now {link}, no documents needed",
                "Your loan is sanctioned. Pay file charge {amt2} and money will be credited instantly {phone}",
            ],
            "ta": [
                "CIBIL இல்லாமல் instant loan {amt}! Aadhaar, PAN மட்டும் போதும், 5 நிமிடத்தில் approval. Processing fee {amt2}-ஐ {upi}-க்கு அனுப்பவும்",
                "உங்களுக்காக {amt} pre approved loan தயாராக உள்ளது. இப்போதே app-ஐ download செய்யுங்கள் {link}, எந்த document-உம் தேவையில்லை",
                "உங்கள் loan sanction ஆகிவிட்டது. File charge {amt2} செலுத்தினால் பணம் உடனே account-ல் வரவு வைக்கப்படும் {phone}",
            ],
        },
        "reward_phish": {
            "en": [
                "Your {bank} reward points worth {amt} expire today, redeem now {link}",
                "{bank} credit card points are about to expire! Convert {amt} to cash, click {link}",
                "Your {app} reward of {amt} is unclaimed, today is the last day. Claim at {link}",
            ],
            "ta": [
                "உங்கள் {bank} reward points மதிப்பு {amt}, இன்று காலாவதியாகிறது, இப்போதே redeem செய்யுங்கள் {link}",
                "{bank} credit card points காலாவதியாகப் போகிறது! {amt}-ஐ cash-ஆக மாற்ற {link} click செய்யுங்கள்",
                "உங்கள் {app} reward {amt} இன்னும் claim செய்யப்படவில்லை, இன்றே கடைசி நாள். Claim செய்ய {link}",
            ],
        },
        "qr_receive": {
            "en": [
                "You have received {amt} from {name}. Scan the QR code at {link} and enter your UPI PIN to receive the money",
                "Buyer for your listing has paid {amt}. Scan the QR code sent on WhatsApp and enter UPI PIN to get the amount",
                "I am an army officer, I will pay advance {amt} for the room. Scan my QR and enter PIN, money will come to you {phone}",
            ],
            "ta": [
                "{name} உங்களுக்கு {amt} அனுப்பியுள்ளார். பணத்தைப் பெற {link}-ல் உள்ள QR code-ஐ scan செய்து UPI PIN உள்ளிடவும்",
                "உங்கள் பொருளை வாங்குபவர் {amt} செலுத்திவிட்டார். WhatsApp-ல் அனுப்பிய QR code-ஐ scan செய்து UPI PIN போட்டால் பணம் வரும்",
                "நான் ஒரு army officer, அறைக்கு advance {amt} தருகிறேன். என் QR-ஐ scan செய்து PIN போடுங்கள், பணம் உங்களுக்கு வரும் {phone}",
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
            "ta": [
                "உங்கள் A/c {acct}-லிருந்து {date} அன்று {amt} VPA {upi}-க்கு debit செய்யப்பட்டது. UPI Ref {ref}. நீங்கள் செய்யவில்லையா? {bank_helpline} அழைக்கவும் -{bank}",
                "{bank}: A/c {acct}-லிருந்து {merchant}-க்கு {amt} debit செய்யப்பட்டது. இருப்பு {amt2}. Ref {ref}",
                "நீங்கள் {app} மூலம் {name}-க்கு {amt} செலுத்தினீர்கள். UPI Ref {ref}. நன்றி",
            ],
        },
        "credit_alert": {
            "en": [
                "Your A/c {acct} is credited with {amt} on {date} from {name} ({upi}). UPI Ref {ref} -{bank}",
                "{amt} has been added to your {app} wallet. Transaction ID {ref}",
                "Salary credit: {amt} credited to your {bank} A/c {acct}. Use {bank} app to check balance",
            ],
            "ta": [
                "உங்கள் A/c {acct}-ல் {date} அன்று {name} ({upi})-லிருந்து {amt} வரவு வைக்கப்பட்டது. UPI Ref {ref} -{bank}",
                "உங்கள் {app} wallet-ல் {amt} சேர்க்கப்பட்டது. Transaction ID {ref}",
                "Salary credit: உங்கள் {bank} A/c {acct}-ல் {amt} வரவு வைக்கப்பட்டது. இருப்பைப் பார்க்க {bank} app-ஐ பயன்படுத்தவும்",
            ],
        },
        "otp": {
            "en": [
                "{otp} is your {bank} OTP for transaction of {amt}. Do not share this OTP with anyone. Bank never asks for OTP",
                "{app} login OTP: {otp}. Valid for 10 mins. Do not share, {app} never calls asking for OTP",
                "Your UPI PIN reset OTP is {otp}. If not requested by you contact {bank_helpline} immediately",
            ],
            "ta": [
                "{amt} transaction-க்கான உங்கள் {bank} OTP {otp}. இந்த OTP-ஐ யாருடனும் பகிர வேண்டாம். வங்கி ஒருபோதும் OTP கேட்காது",
                "{app} login OTP: {otp}. 10 நிமிடங்கள் செல்லுபடியாகும். யாரிடமும் சொல்ல வேண்டாம், {app} call செய்து OTP கேட்காது",
                "உங்கள் UPI PIN reset OTP {otp}. நீங்கள் request செய்யவில்லை என்றால் உடனே {bank_helpline} தொடர்பு கொள்ளவும்",
            ],
        },
        "collect_genuine": {
            "en": [
                "{merchant} has sent you a payment request of {amt} on {app}. Approve in app if you placed the order, else decline",
                "{name} has requested {amt} on {app}. Remember, you never need to enter PIN to RECEIVE money",
                "Payment request: {company} bill {amt}, due date {date}. Pay via {app} app",
            ],
            "ta": [
                "{merchant} உங்களுக்கு {app}-ல் {amt} payment request அனுப்பியுள்ளது. நீங்கள் order செய்திருந்தால் app-ல் approve செய்யுங்கள், இல்லையெனில் decline செய்யுங்கள்",
                "{name} {app}-ல் {amt} request அனுப்பியுள்ளார். நினைவில் கொள்ளுங்கள், பணம் பெற PIN போட வேண்டியதில்லை",
                "Payment request: {company} bill {amt}, கடைசி தேதி {date}. {app} app மூலம் செலுத்தவும்",
            ],
        },
        "autopay_mandate": {
            "en": [
                "{merchant} has created a UPI AutoPay mandate of {amt} on {app}. It will debit monthly from {date}. Manage in {app} app",
                "Your {app} AutoPay for {company2} recharge of {amt} will be executed on {date}. To cancel, open {app} and go to AutoPay",
                "Reminder: UPI AutoPay of {amt} to {merchant} is scheduled for {date} -{bank}",
            ],
            "ta": [
                "{merchant} {app}-ல் {amt}-க்கான UPI AutoPay mandate உருவாக்கியுள்ளது. {date} முதல் மாதந்தோறும் debit ஆகும். {app} app-ல் நிர்வகிக்கலாம்",
                "{company2} recharge {amt}-க்கான உங்கள் {app} AutoPay {date} அன்று நடைபெறும். ரத்து செய்ய {app}-ல் AutoPay பகுதிக்குச் செல்லவும்",
                "நினைவூட்டல்: {merchant}-க்கு {amt} UPI AutoPay {date} அன்று திட்டமிடப்பட்டுள்ளது -{bank}",
            ],
        },
        "personal": {
            "en": [
                "Hey send the {amt} for yesterday's dinner to {upi} whenever free",
                "Mom sent {amt} on GPay, check once",
                "Hi {name}, I have transferred {amt}, sending screenshot. Ref {ref}",
                "Will send this month's rent {amt} a bit late, by {date} for sure",
            ],
            "ta": [
                "டேய், நேற்று dinner-க்கான {amt}-ஐ நேரம் கிடைக்கும்போது {upi}-க்கு அனுப்பிவிடு",
                "அம்மா GPay-ல் {amt} அனுப்பியிருக்காங்க, ஒருமுறை check பண்ணு",
                "Hi {name}, நான் {amt} transfer பண்ணிட்டேன், screenshot அனுப்புறேன். Ref {ref}",
                "இந்த மாச rent {amt} கொஞ்சம் late-ஆ அனுப்புவேன், {date}-க்குள் கண்டிப்பா",
            ],
        },
        "security_advisory": {
            "en": [
                "{bank} never asks for your PIN, OTP or CVV over call/SMS. For KYC update visit branch or use official app only",
                "Beware! UPI PIN is not required to receive money. Do not click unknown links -{bank}",
                "RBI says: report fraud calls at 1930. Update your KYC only at {bank} branch",
            ],
            "ta": [
                "{bank} ஒருபோதும் call/SMS மூலம் உங்கள் PIN, OTP அல்லது CVV கேட்காது. KYC update-க்கு branch-க்குச் செல்லுங்கள் அல்லது official app-ஐ மட்டும் பயன்படுத்துங்கள்",
                "எச்சரிக்கை! பணம் பெற UPI PIN தேவையில்லை. தெரியாத link-களை click செய்ய வேண்டாம் -{bank}",
                "RBI: மோசடி அழைப்புகளை 1930-ல் புகார் செய்யுங்கள். உங்கள் KYC-ஐ {bank} branch-ல் மட்டுமே update செய்யுங்கள்",
            ],
        },
        "bill_paid": {
            "en": [
                "Your {company} bill of {amt} is paid successfully. Transaction ID {ref}. Thank you",
                "Payment of {amt} for your {merchant} order is successful. Order will be delivered by {date}",
                "Your {app} recharge of {amt} is successful. Validity {days} days. Ref {ref}",
            ],
            "ta": [
                "உங்கள் {company} bill {amt} வெற்றிகரமாக செலுத்தப்பட்டது. Transaction ID {ref}. நன்றி",
                "உங்கள் {merchant} order-க்கான {amt} payment வெற்றிகரமாக முடிந்தது. Order {date}-க்குள் deliver செய்யப்படும்",
                "உங்கள் {app} recharge {amt} வெற்றிகரமாக முடிந்தது. Validity {days} நாட்கள். Ref {ref}",
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
            "ta": [
                "{merchant}-ல் {app} மூலம் பணம் செலுத்தி {pct}% cashback பெறுங்கள், அதிகபட்சம் {amt}. Offer {date} வரை. T&C apply",
                "இன்று மட்டும்! {app}-ல் bill செலுத்தி {amt} வரை cashback வெல்லுங்கள். இப்போதே திறக்கவும் {link}",
                "Super offer: {merchant}-ல் UPI payment-க்கு flat {amt} cashback. *T&C",
            ],
        },
        "sale_offer": {
            "en": [
                "{merchant} Festive sale is live! Up to {pct}% off on all products. Shop now {link}",
                "Big sale alert! {pct}% off on electronics at {merchant} for {days} days only. T&C",
                "Flat {pct}% off on new collection, visit {merchant} store or order at {link}",
            ],
            "ta": [
                "{merchant} தீபாவளி sale தொடங்கிவிட்டது! அனைத்து பொருட்களுக்கும் {pct}% வரை தள்ளுபடி. Shop now {link}",
                "Big sale alert! {merchant}-ல் electronics-க்கு {pct}% off, {days} நாட்கள் மட்டும். T&C",
                "புதிய collection-க்கு flat {pct}% தள்ளுபடி, {merchant} store-க்கு வாருங்கள் அல்லது {link}-ல் order செய்யுங்கள்",
            ],
        },
        "loan_promo": {
            "en": [
                "{bank}: Pre-approved personal loan up to {amt} at attractive rates. Apply on {bank} app. T&C apply",
                "{bank} Gold loan now at just {rate}% interest. Visit nearest branch",
                "Fulfil your dream home with {bank} home loan. Low EMI, quick approval. {link}",
            ],
            "ta": [
                "{bank}: உங்களுக்கு {amt} வரை pre-approved personal loan, குறைந்த வட்டியில். {bank} app-ல் apply செய்யுங்கள். T&C apply",
                "{bank} Gold loan இப்போது {rate}% வட்டியில் மட்டுமே. அருகிலுள்ள branch-க்கு வாருங்கள்",
                "{bank} home loan உடன் உங்கள் சொந்த வீட்டுக் கனவை நனவாக்குங்கள். குறைந்த EMI, விரைவான approval. {link}",
            ],
        },
        "recharge_plan": {
            "en": [
                "{company2} new plan: {amt} for 2GB/day, unlimited calls, {days} days validity. Recharge on {app}",
                "Your {company2} plan expires in {days} days. Recharge now and enjoy unlimited data {link}",
                "Special offer: extra 10GB data free on {amt} recharge. Hurry!",
            ],
            "ta": [
                "{company2} புதிய plan: {amt}-க்கு தினமும் 2GB, unlimited calls, {days} நாட்கள் validity. {app}-ல் recharge செய்யுங்கள்",
                "உங்கள் {company2} plan {days} நாட்களில் முடிவடைகிறது. இப்போதே recharge செய்து unlimited data அனுபவியுங்கள் {link}",
                "Special offer: {amt} recharge-க்கு கூடுதல் 10GB data இலவசம். சீக்கிரம்!",
            ],
        },
        "rewards_points": {
            "en": [
                "Your {bank} credit card reward points will expire on {date}. Redeem them on {bank} app",
                "You won a {app} scratch card! Check rewards section in your {app} app",
                "You have coins worth {amt} in your {merchant} wallet, use them on your next purchase. Valid {days} days",
            ],
            "ta": [
                "உங்கள் {bank} credit card reward points {date} அன்று காலாவதியாகும். {bank} app-ல் redeem செய்யுங்கள்",
                "நீங்கள் {app} scratch card வென்றுள்ளீர்கள்! உங்கள் {app} app-ல் rewards பகுதியைப் பாருங்கள்",
                "உங்கள் {merchant} wallet-ல் {amt} மதிப்புள்ள coins உள்ளன, அடுத்த shopping-ல் பயன்படுத்துங்கள். {days} நாட்கள் செல்லுபடியாகும்",
            ],
        },
    },
}

from .templates_hi import HI as _HI

for _label, _subs in _HI.items():
    for _sub, _lst in _subs.items():
        assert len(_lst) == len(TEMPLATES[_label][_sub]["en"]), (_label, _sub)
        TEMPLATES[_label][_sub]["hi"] = _lst

LANGS = ["en", "hi", "ta"]
LANG_NAMES = {"en": "English", "hi": "Hindi–English", "ta": "Tamil–English"}
# script of the non-English part of each code-mixed setting
LANG_SCRIPT = {"hi": "deva", "ta": "taml"}
LABELS = ["legit", "promo", "scam"]
