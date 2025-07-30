import React, { useState, useEffect } from 'react';
import { X, Heart, Sparkles, Star, Smile, Gift, Zap, Palette, Rocket, ShoppingBag, ThumbsUp } from 'lucide-react';

// Interfaces
interface FeedbackPopupProps {
  isVisible: boolean;
  onClose: () => void;
}

interface FeedbackData {
  initialReaction: string;
  styleVibe: string;
  purchaseLikelihood: number;
  wouldRecommend: boolean;
  additionalThoughts: string;
}

// Main Component
const FeedbackPopup: React.FC<FeedbackPopupProps> = ({ isVisible, onClose }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackData, setFeedbackData] = useState<FeedbackData>({
    initialReaction: '',
    styleVibe: '',
    purchaseLikelihood: 0,
    wouldRecommend: false,
    additionalThoughts: ''
  });

  // Reset state on visibility change
  useEffect(() => {
    if (isVisible) {
      setCurrentStep(1);
      setIsSubmitted(false);
      setFeedbackData({
        initialReaction: '',
        styleVibe: '',
        purchaseLikelihood: 0,
        wouldRecommend: false,
        additionalThoughts: ''
      });
    }
  }, [isVisible]);

  if (!isVisible) return null;

  // Handlers
  const handleSelect = (field: keyof FeedbackData, value: any, nextStep: number) => {
    setFeedbackData(prev => ({ ...prev, [field]: value }));
    setCurrentStep(nextStep);
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    console.log("Submitting final feedback:", feedbackData);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsSubmitting(false);
    setIsSubmitted(true);
    setTimeout(onClose, 4000); // Auto-close after reward
  };



  // Step 1: Initial Reaction
  const renderStep1 = () => (
    <div className="feedback-step">
      <Palette className="feedback-icon-lg text-pink-500" />
      <h3 className="feedback-title">What was your first reaction?</h3>
      <p className="feedback-subtitle">First impressions count! 💖</p>
      <div className="feedback-grid">
        <button className="feedback-option" onClick={() => handleSelect('initialReaction', 'love', 2)}>😍 Love it!</button>
        <button className="feedback-option" onClick={() => handleSelect('initialReaction', 'like', 2)}>😊 Like it</button>
        <button className="feedback-option" onClick={() => handleSelect('initialReaction', 'unsure', 2)}>🤔 Unsure</button>
      </div>
    </div>
  );

  // Step 2: Style Vibe
  const renderStep2 = () => (
    <div className="feedback-step">
      <Sparkles className="feedback-icon-lg text-purple-500" />
      <h3 className="feedback-title">How would you describe the style?</h3>
      <p className="feedback-subtitle">This helps us learn your aesthetic. ✨</p>
      <div className="feedback-grid">
        <button className="feedback-option" onClick={() => handleSelect('styleVibe', 'trendy', 3)}>🚀 Trendy & Bold</button>
        <button className="feedback-option" onClick={() => handleSelect('styleVibe', 'classic', 3)}> timeless</button>
        <button className="feedback-option" onClick={() => handleSelect('styleVibe', 'casual', 3)}>👟 Casual & Comfy</button>
      </div>
    </div>
  );

  // Step 3: Purchase Likelihood
  const renderStep3 = () => (
    <div className="feedback-step">
      <ShoppingBag className="feedback-icon-lg text-green-500" />
      <h3 className="feedback-title">How likely are you to buy something like this?</h3>
      <p className="feedback-subtitle">From 'window shopping' to 'add to cart'. 🛍️</p>
      <div className="flex justify-center items-center gap-2 mt-4">
        {[1, 2, 3, 4, 5].map(level => (
          <button 
            key={level} 
            onClick={() => handleSelect('purchaseLikelihood', level, 4)} 
            className={`feedback-star-button ${feedbackData.purchaseLikelihood >= level ? 'toggled' : ''}`}>
            <Star className="w-7 h-7" />
          </button>
        ))}
      </div>
    </div>
  );

  // Step 4: Recommendation and Final Thoughts
  const renderStep4 = () => (
    <div className="feedback-step">
      <ThumbsUp className="feedback-icon-lg text-blue-500" />
      <h3 className="feedback-title">Would you recommend us to a friend?</h3>
      <p className="feedback-subtitle">Your opinion helps us grow. 🙏</p>
      <div className="flex justify-center gap-4 mt-4">
        <button onClick={() => setFeedbackData(prev => ({...prev, wouldRecommend: true}))} className={`feedback-thumb-option ${feedbackData.wouldRecommend ? 'toggled-yes' : ''}`}>👍 Yes</button>
        <button onClick={() => setFeedbackData(prev => ({...prev, wouldRecommend: false}))} className={`feedback-thumb-option ${!feedbackData.wouldRecommend ? 'toggled-no' : ''}`}>👎 No</button>
      </div>
      <textarea
        placeholder="Any other thoughts? (optional)"
        value={feedbackData.additionalThoughts}
        onChange={(e) => setFeedbackData(prev => ({ ...prev, additionalThoughts: e.target.value }))}
        className="feedback-textarea"
      />
      <button onClick={handleSubmit} disabled={isSubmitting} className="feedback-submit-button">
        {isSubmitting ? <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto"></div> : 'Complete & Get Reward'}
      </button>
    </div>
  );

  // Success/Reward Screen
  const renderSuccess = () => (
    <div className="feedback-step text-center">
      <Gift className="feedback-icon-lg text-yellow-500 animate-float" />
      <h3 className="text-3xl font-bold text-gray-800 mb-2">Thank You! 💖</h3>
      <p className="text-gray-600 mb-4">Your feedback unlocks better recommendations and a special reward!</p>
      <div className="bg-purple-100/50 border border-purple-200/50 rounded-lg p-4 inline-block">
        <p className="text-lg font-semibold text-purple-700">✨ 15% OFF Your Next Purchase ✨</p>
      </div>
    </div>
  );

  return (
    <div className={`feedback-overlay ${isVisible ? 'visible' : ''}`}>
      <div className={`feedback-container ${isVisible ? 'visible' : ''}`}>
        {/* Header */}
        <div className="feedback-header">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center shadow-lg">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-gray-800 text-lg">Share Your Style Insights</span>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-purple-100 rounded-full transition-all duration-200 group">
            <X className="h-5 w-5 text-gray-500 group-hover:text-purple-600" />
          </button>
        </div>

        {/* Progress Bar */}
        {!isSubmitted && (
          <div className="px-6 pt-4">
            <div className="w-full bg-gray-200 rounded-full h-2.5 shadow-inner">
              <div 
                className="bg-gradient-to-r from-purple-500 to-pink-500 h-2.5 rounded-full transition-all duration-500 shadow-sm"
                style={{ width: `${(currentStep / 4) * 100}%` }}
              />
            </div>
            <div className="text-right mt-1 text-xs text-purple-600 font-medium">
              Step {currentStep} of 4
            </div>
          </div>
        )}

        {/* Content Area - GUARANTEED NO SCROLLBAR */}
        <div className="p-6 overflow-hidden min-h-[350px] flex items-center justify-center">
          {isSubmitted ? renderSuccess() : (
            <div className="w-full">
              {currentStep === 1 && renderStep1()}
              {currentStep === 2 && renderStep2()}
              {currentStep === 3 && renderStep3()}
              {currentStep === 4 && renderStep4()}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default FeedbackPopup;
