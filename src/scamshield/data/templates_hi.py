"""
Hindi–English templates for UPI-MixSMS (language code "hi").

Hindi is written in Devanagari script and the English banking vocabulary (KYC, account, link,
OTP, PIN, refund, app and bank names ...) stays in Latin script, as separate words followed by
Hindi postpositions ("account में", "link पर click करें"). Romanised Hindi ("Hinglish") is not
a language setting; it only appears as the L4 transliteration attack.

Each list is parallel to the English list of the same subtype (same intent, same slots, same
number of templates), so the template-disjoint split holds out the same template index in
every language.
"""

HI = {
    "scam": {
        "kyc_block": [
            "प्रिय ग्राहक, आपका {bank} account आज रात 12 बजे block कर दिया जाएगा। तुरंत KYC update करने के लिए इस link पर click करें {link}",
            "{bank} ALERT: आपका PAN card link नहीं है, account suspend हो जाएगा। अभी update करें {link}",
            "आपका KYC expire हो गया है। {app} wallet बंद होने से बचाने के लिए तुरंत {phone} पर call करें",
        ],
        "refund_collect": [
            "बधाई हो! आपको {amt} cashback मिला है। पैसे पाने के लिए {app} पर आई request accept करें और UPI PIN डालें",
            "आपका {amt} का refund pending है। पाने के लिए collect request approve करें और PIN enter करें। Ref {ref}",
            "{merchant} का {amt} refund आपके account में आ रहा है, बस {upi} से आई request पर PIN डालें",
        ],
        "lottery_prize": [
            "बधाई हो! KBC lucky draw में आपका नंबर चुना गया है, इनाम {prize}। Registration fee {amt} {upi} पर भेजें",
            "आपने {app} mega contest में {prize} जीते हैं! पाने के लिए {link} पर अपनी जानकारी भरें, offer सिर्फ {days} दिन",
            "Airtel lucky winner: आपके नंबर ने {prize} जीते हैं। अभी WhatsApp करें {phone}",
        ],
        "wrong_transfer": [
            "भाई, गलती से आपके account में {amt} transfer हो गए, कृपया {upi} पर वापस भेज दो, बहुत urgent है",
            "Sir, मैंने गलत नंबर पर {amt} भेज दिए, screenshot देखिए। कृपया {upi} पर return कर दीजिए",
            "Hello, मेरे {amt} गलती से आपको चले गए, वापस नहीं किए तो police complaint करूँगा {phone}",
        ],
        "job_task": [
            "Part time job! घर बैठे रोज़ {job_amt} कमाएँ, बस YouTube videos like करने हैं। WhatsApp {phone}",
            "Amazon work from home: रोज़ की कमाई {job_amt}, joining fee सिर्फ {amt}। अभी register करें {link}",
            "नमस्ते, मैं HR से बोल रही हूँ, आपका resume shortlist हुआ है। छोटे task पूरे करके {job_amt} कमाएँ, Telegram पर join करें {link}",
        ],
        "bill_disconnect": [
            "प्रिय उपभोक्ता, पिछला bill update न होने के कारण आपका {company} बिजली connection आज रात 9:30 बजे काट दिया जाएगा। तुरंत {phone} पर call करें",
            "{company}: आपका bill बकाया है और connection काट दिया जाएगा। अभी {amt} भरें {link}",
            "Dear consumer, आज रात आपकी बिजली काट दी जाएगी। Electricity officer से संपर्क करें {phone}",
        ],
        "parcel_customs": [
            "{courier}: आपका parcel customs में रोका गया है। Release fee {amt} भरें {link}",
            "गलत पते के कारण आपका package deliver नहीं हो सका। 24 घंटे में address update करें {link}",
            "आपके नाम के parcel में गैरकानूनी सामान मिलने पर airport पर ज़ब्त किया गया है। तुरंत {phone} पर call करें वरना FIR दर्ज होगी",
        ],
        "fake_support": [
            "{app} customer care: आपका transaction fail हो गया, refund के लिए AnyDesk app download करें और {phone} पर call करें",
            "आपके {bank} credit card पर {amt} का संदिग्ध transaction हुआ है। Cancel करने के लिए OTP बताएँ, call {phone}",
            "हम {bank} head office से बोल रहे हैं, आपका debit card block हो गया है, unblock के लिए card number और CVV reply करें",
        ],
        "loan_instant": [
            "बिना CIBIL के instant loan {amt}! सिर्फ Aadhaar और PAN से 5 मिनट में approval। Processing fee {amt2} {upi} पर भेजें",
            "आपके लिए {amt} का pre approved loan तैयार है। अभी app download करें {link}, कोई document नहीं चाहिए",
            "आपका loan sanction हो गया है। File charge {amt2} भरें और पैसे तुरंत आपके account में आ जाएँगे {phone}",
        ],
        "reward_phish": [
            "आपके {bank} reward points जिनकी कीमत {amt} है, आज expire हो रहे हैं, अभी redeem करें {link}",
            "{bank} credit card points expire होने वाले हैं! {amt} को cash में बदलने के लिए {link} पर click करें",
            "आपका {app} reward {amt} अभी तक claim नहीं हुआ, आज आखिरी दिन है। Claim करें {link}",
        ],
        "qr_receive": [
            "{name} ने आपको {amt} भेजे हैं। पैसे पाने के लिए {link} पर QR code scan करें और UPI PIN डालें",
            "आपके सामान के खरीदार ने {amt} भेज दिए हैं। WhatsApp पर भेजा QR code scan करें और UPI PIN डालें, पैसे आ जाएँगे",
            "मैं army officer हूँ, कमरे के लिए advance {amt} दूँगा। मेरा QR scan करके PIN डालें, पैसे आपको आ जाएँगे {phone}",
        ],
    },
    "legit": {
        "debit_alert": [
            "आपके A/c {acct} से {date} को {amt} VPA {upi} को debit किए गए। UPI Ref {ref}। आपने नहीं किया? {bank_helpline} पर call करें -{bank}",
            "{bank}: A/c {acct} से {merchant} के लिए {amt} debit हुए। शेष राशि {amt2}। Ref {ref}",
            "आपने {app} से {name} को {amt} भेजे। UPI Ref {ref}। धन्यवाद",
        ],
        "credit_alert": [
            "आपके A/c {acct} में {date} को {name} ({upi}) से {amt} जमा हुए। UPI Ref {ref} -{bank}",
            "आपके {app} wallet में {amt} जोड़े गए। Transaction ID {ref}",
            "Salary credit: आपके {bank} A/c {acct} में {amt} जमा हुए। Balance देखने के लिए {bank} app इस्तेमाल करें",
        ],
        "otp": [
            "{amt} के transaction के लिए आपका {bank} OTP {otp} है। यह OTP किसी से share न करें। बैंक कभी OTP नहीं माँगता",
            "{app} login OTP: {otp}। 10 मिनट तक valid। किसी को न बताएँ, {app} कभी call करके OTP नहीं माँगता",
            "आपका UPI PIN reset OTP {otp} है। अगर आपने request नहीं की तो तुरंत {bank_helpline} से संपर्क करें",
        ],
        "collect_genuine": [
            "{merchant} ने {app} पर आपको {amt} की payment request भेजी है। Order आपने किया है तो app में approve करें, वरना decline करें",
            "{name} ने {app} पर {amt} की request भेजी है। याद रखें, पैसे पाने के लिए PIN डालने की ज़रूरत नहीं होती",
            "Payment request: {company} bill {amt}, आखिरी तारीख {date}। {app} app से भुगतान करें",
        ],
        "autopay_mandate": [
            "{merchant} ने {app} पर {amt} का UPI AutoPay mandate बनाया है। {date} से हर महीने debit होगा। {app} app में manage करें",
            "{company2} recharge {amt} के लिए आपका {app} AutoPay {date} को होगा। Cancel करने के लिए {app} में AutoPay section में जाएँ",
            "याद दिलाना: {merchant} को {amt} का UPI AutoPay {date} को scheduled है -{bank}",
        ],
        "personal": [
            "अरे, कल के dinner के {amt} जब time मिले {upi} पर भेज देना",
            "मम्मी ने GPay पर {amt} भेजे हैं, एक बार check कर लेना",
            "Hi {name}, मैंने {amt} transfer कर दिए, screenshot भेज रहा हूँ। Ref {ref}",
            "इस महीने का rent {amt} थोड़ा late भेजूँगा, {date} तक पक्का",
        ],
        "security_advisory": [
            "{bank} कभी भी call/SMS पर आपका PIN, OTP या CVV नहीं माँगता। KYC update के लिए branch जाएँ या सिर्फ official app इस्तेमाल करें",
            "सावधान! पैसे पाने के लिए UPI PIN की ज़रूरत नहीं होती। अनजान link पर click न करें -{bank}",
            "RBI: धोखाधड़ी वाली calls की शिकायत 1930 पर करें। अपना KYC सिर्फ {bank} branch में update करें",
        ],
        "bill_paid": [
            "आपका {company} bill {amt} सफलतापूर्वक भर दिया गया। Transaction ID {ref}। धन्यवाद",
            "आपके {merchant} order के लिए {amt} का payment सफल रहा। Order {date} तक deliver होगा",
            "आपका {app} recharge {amt} सफल रहा। Validity {days} दिन। Ref {ref}",
        ],
    },
    "promo": {
        "cashback_offer": [
            "{merchant} पर {app} से payment करें और {pct}% cashback पाएँ, अधिकतम {amt}। Offer {date} तक। T&C apply",
            "सिर्फ आज! {app} पर bill भरें और {amt} तक cashback जीतें। अभी खोलें {link}",
            "Super offer: {merchant} पर UPI payment पर flat {amt} cashback। *T&C",
        ],
        "sale_offer": [
            "{merchant} festive sale शुरू हो गई है! सभी products पर {pct}% तक की छूट। Shop now {link}",
            "Big sale alert! {merchant} पर electronics पर {pct}% off, सिर्फ {days} दिन। T&C",
            "नई collection पर flat {pct}% छूट, {merchant} store आएँ या {link} पर order करें",
        ],
        "loan_promo": [
            "{bank}: आपके लिए {amt} तक का pre-approved personal loan, आकर्षक ब्याज दर पर। {bank} app पर apply करें। T&C apply",
            "{bank} Gold loan अब सिर्फ {rate}% ब्याज पर। नज़दीकी branch में आएँ",
            "{bank} home loan के साथ अपने घर का सपना पूरा करें। कम EMI, जल्दी approval। {link}",
        ],
        "recharge_plan": [
            "{company2} नया plan: {amt} में रोज़ 2GB, unlimited calls, {days} दिन validity। {app} पर recharge करें",
            "आपका {company2} plan {days} दिन में खत्म हो रहा है। अभी recharge करें और unlimited data का मज़ा लें {link}",
            "Special offer: {amt} के recharge पर 10GB data मुफ़्त। जल्दी करें!",
        ],
        "rewards_points": [
            "आपके {bank} credit card reward points {date} को expire होंगे। {bank} app पर redeem करें",
            "आपने {app} scratch card जीता है! अपने {app} app में rewards section देखें",
            "आपके {merchant} wallet में {amt} के coins हैं, अगली खरीदारी पर इस्तेमाल करें। {days} दिन valid",
        ],
    },
}
