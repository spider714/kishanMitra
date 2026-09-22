
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sprout, Phone, User, MapPin, KeyRound, ArrowRight, Loader2, Wheat, Layers } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useLanguage } from "@/contexts/LanguageContext";


export default function OnboardingPage() {
  const [step, setStep] = useState<"login" | "otp">("login");
  const [username, setUsername] = useState("");
  const [phone, setPhone] = useState("");
  const [district, setDistrict] = useState("RAIPUR");
  const [state, setState] = useState("Chhattisgarh");
  const [landSize, setLandSize] = useState("1 ACRES");
  const [category, setCategory] = useState("OBC");
  const [crops, setCrops] = useState("Wheat, Paddy");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { t, lang, setLang } = useLanguage();


  const handleSendOtp = () => {
    if (!username.trim() || !phone.trim() || phone.length < 10) return;
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      setStep("otp");
    }, 1000);
  };

  const handleOtpChange = (value: string, index: number) => {
    if (value.length > 1) return;
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleOtpKeyDown = (e: React.KeyboardEvent, index: number) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      prevInput?.focus();
    }
  };

  const handleVerifyOtp = async () => {
    const otpValue = otp.join("");
    if (otpValue.length < 6) return;
    setIsLoading(true);

    const profileData = {
      name: username.trim(),
      phone: phone.trim(),
      district: district.trim() || "RAIPUR",
      state: state.trim() || "Chhattisgarh",
      landSize: landSize.trim() || "1 ACRES",
      category: category || "OBC",
      crops: crops.trim() || "Wheat, Paddy",
    };

    // Save details to localStorage
    localStorage.setItem("app_language", "hi");
    localStorage.setItem("user_name", profileData.name);
    localStorage.setItem("user_phone", profileData.phone);
    localStorage.setItem("user_district", profileData.district);
    localStorage.setItem("user_state", profileData.state);
    localStorage.setItem("user_land_size", profileData.landSize);
    localStorage.setItem("user_category", profileData.category);
    localStorage.setItem("user_crops", profileData.crops);

    // Call Backend API to sync profile
    try {
      await fetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profileData),
      });
    } catch (e) {
      console.warn("Backend profile sync failed:", e);
    }

    setTimeout(() => {
      setIsLoading(false);
      navigate("/home");
    }, 800);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-gradient-to-b from-green-50 via-slate-50 to-emerald-50">
      {/* Logo & Title */}
      <div className="text-center mb-5">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 border border-emerald-300 text-emerald-700 rounded-full mb-3 shadow-sm">
          <Sprout className="w-9 h-9" />
        </div>
        <h1 className="text-2xl font-bold text-slate-800">Kisanमित्र</h1>
        <p className="text-sm text-primary font-semibold">किसान मित्र</p>
      </div>

      {/* Login Card */}
      <div className="w-full max-w-md bg-white p-6 rounded-3xl shadow-lg border border-slate-200">
        {step === "login" && (
          <>
            <div className="mb-5 border-b border-slate-100 pb-3">
              <h2 className="text-xl font-bold text-slate-800">किसान पंजीकरण / Login</h2>
              <p className="text-xs text-slate-500 mt-1">
                योजना पात्रता एवं प्रोफाइल के लिए अपनी सही जानकारी भरें
              </p>
            </div>

            {/* 1. Full Name */}
            <div className="mb-4">
              <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wide">
                Full Name / पूरा नाम *
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="उदा: Ramesh Kumar"
                  className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-slate-800 font-medium"
                />
              </div>
            </div>

            {/* 2. Phone Number */}
            <div className="mb-4">
              <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wide">
                Mobile Number / मोबाइल नंबर *
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <span className="absolute left-9 top-1/2 -translate-y-1/2 text-xs text-slate-500 font-bold">+91</span>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/\D/g, "").slice(0, 10))}
                  placeholder="10 अंकों का नंबर (उदा: 5513112551)"
                  maxLength={10}
                  className="w-full pl-16 pr-3 py-2.5 border border-slate-300 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-slate-800 font-medium"
                />
              </div>
            </div>

            {/* 3. District & State Grid */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wide">
                  District / जिला *
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={district}
                    onChange={(e) => setDistrict(e.target.value)}
                    placeholder="RAIPUR"
                    className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-slate-800 font-medium"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wide">
                  State / राज्य *
                </label>
                <input
                  type="text"
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  placeholder="Chhattisgarh"
                  className="w-full px-3 py-2.5 border border-slate-300 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-slate-800 font-medium"
                />
              </div>
            </div>

            {/* 4. Land Size & Category Grid */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wide">
                  Land Size / जमीन *
                </label>
                <div className="relative">
                  <Layers className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={landSize}
                    onChange={(e) => setLandSize(e.target.value)}
                    placeholder="1 ACRES"
                    className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-slate-800 font-medium"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wide">
                  Category / वर्ग *
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2.5 border border-slate-300 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-slate-800 font-medium"
                >
                  <option value="General">General</option>
                  <option value="OBC">OBC</option>
                  <option value="SC">SC</option>
                  <option value="ST">ST</option>
                </select>
              </div>
            </div>

            {/* 5. Primary Crops */}
            <div className="mb-6">
              <label className="block text-xs font-bold text-slate-700 mb-1 uppercase tracking-wide">
                Primary Crops / प्रमुख फसलें *
              </label>
              <div className="relative">
                <Wheat className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={crops}
                  onChange={(e) => setCrops(e.target.value)}
                  placeholder="Wheat, Paddy"
                  className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-sm text-slate-800 font-medium"
                />
              </div>
            </div>

            {/* Send OTP Button */}
            <Button
              fullWidth
              disabled={!username.trim() || phone.length < 10 || isLoading}
              onClick={handleSendOtp}
              className="h-12 text-base flex items-center justify-center gap-2 shadow-md"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  OTP भेज रहे हैं...
                </>
              ) : (
                <>
                  OTP प्राप्त करें (Send OTP) <ArrowRight className="w-5 h-5" />
                </>
              )}
            </Button>
          </>
        )}

        {step === "otp" && (
          <>
            <div className="text-center mb-6">
              <h2 className="text-xl font-bold text-slate-800 mb-1">OTP सत्यापन</h2>
              <p className="text-xs text-slate-500">
                +91 {phone} पर भेजा गया 6-अंकों का ओटीपी दर्ज करें
              </p>
            </div>

            {/* OTP Inputs */}
            <div className="flex gap-2 justify-center mb-6">
              {otp.map((digit, idx) => (
                <input
                  key={idx}
                  id={`otp-${idx}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleOtpChange(e.target.value, idx)}
                  onKeyDown={(e) => handleOtpKeyDown(e, idx)}
                  className="w-11 h-13 text-center text-xl font-bold border border-slate-300 rounded-xl bg-slate-50 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white text-slate-800"
                />
              ))}
            </div>

            <p className="text-center text-xs text-slate-500 mb-6">
              OTP नहीं मिला?{" "}
              <button
                onClick={() => { setOtp(["", "", "", "", "", ""]); handleSendOtp(); }}
                className="text-primary font-bold hover:underline"
              >
                दोबारा भेजें (Resend)
              </button>
            </p>

            <Button
              fullWidth
              disabled={otp.join("").length < 6 || isLoading}
              onClick={handleVerifyOtp}
              className="h-12 text-base flex items-center justify-center gap-2 mb-3 shadow-md"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  सत्यापित कर रहे हैं...
                </>
              ) : (
                <>
                  <KeyRound className="w-5 h-5" />
                  सत्यापित करें और लॉगिन करें
                </>
              )}
            </Button>

            <button
              onClick={() => { setStep("login"); setOtp(["", "", "", "", "", ""]); }}
              className="w-full text-center text-xs font-bold text-slate-500 hover:text-primary transition-colors"
            >
              ← जानकारी बदलें (Edit Info)
            </button>
          </>
        )}
      </div>
    </div>
  );
}

