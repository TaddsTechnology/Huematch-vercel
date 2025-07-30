import React, { useState } from 'react';
import { X, Heart, Sparkles, Star, ThumbsUp, ThumbsDown, Smile, Frown, MessageCircle } from 'lucide-react';

interface FeedbackPopupProps {
  isVisible: boolean;
  onClose: () => void;
  userContext?: {
    monkSkinTone?: string;
    activeTab?: string;
    sessionId?: string;
  };
}

interface FeedbackData {
  feelingResponse: string;
  confidenceLevel: number;
  styleMatch: string;
  recommendation: boolean;
  additionalThoughts: string;
}

const FeedbackPopup: React.FC<FeedbackPopupProps> = ({ isVisible, onClose }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [feedbackData, setFeedbackData] = useState<FeedbackData>({
    feelingResponse: '',
    confidenceLevel: 0,
    styleMatch: '',
    recommendation: false,
    additionalThoughts: ''
  });

  if (!isVisible) return null;

  const handleFeelingSelect = (feeling: string) => {
    setFeedbackData(prev => ({ ...prev, feelingResponse: feeling }));
    setCurrentStep(2);
  };

  const handleConfidenceSelect = (level: number) => {
    setFeedbackData(prev => ({ ...prev, confidenceLevel: level }));
    setCurrentStep(3);
  };

  const handleStyleMatchSelect = (match: string) => {
    setFeedbackData(prev => ({ ...prev, styleMatch: match }));
    setCurrentStep(4);
  };

  const handleRecommendationSelect = (rec: boolean) => {
    setFeedbackData(prev => ({ ...prev, recommendation: rec }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    console.log("Submitting feedback:", feedbackData);
    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsSubmitted(true);
    setTimeout(() => {
      onClose();
    }, 3000);
  };

  const renderStep1 = () => (
    <div className="text-center">
      <Sparkles className="h-12 w-12 text-yellow-400 mx-auto mb-4" />
      <h3 className="text-xl font-bold text-gray-800 mb-2">How did these recommendations make you feel?</h3>
      <div className="flex justify-center gap-4 mt-4">
        <button onClick={() => handleFeelingSelect('Inspired')} className="p-4 bg-purple-100 rounded-lg hover:bg-purple-200 transition-colors">🎨 Inspired</button>
        <button onClick={() => handleFeelingSelect('Hopeful')} className="p-4 bg-pink-100 rounded-lg hover:bg-pink-200 transition-colors">💖 Hopeful</button>
        <button onClick={() => handleFeelingSelect('Unsure')} className="p-4 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">🤔 Unsure</button>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="text-center">
      <Star className="h-12 w-12 text-yellow-400 mx-auto mb-4" />
      <h3 className="text-xl font-bold text-gray-800 mb-2">How much did these recommendations boost your confidence?</h3>
      <div className="flex justify-center items-center gap-2 mt-4">
        <span>Not at all</span>
        {[1, 2, 3, 4, 5].map(level => (
          <button key={level} onClick={() => handleConfidenceSelect(level)} className={`w-10 h-10 rounded-full transition-all ${feedbackData.confidenceLevel >= level ? 'bg-yellow-400 scale-110' : 'bg-gray-200'}`}>
            {level}
          </button>
        ))}
        <span>A lot!</span>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="text-center">
      <Heart className="h-12 w-12 text-red-500 mx-auto mb-4" />
      <h3 className="text-xl font-bold text-gray-800 mb-2">Do these recommendations feel like 'you'?</h3>
      <div className="space-y-3 mt-4">
        <button onClick={() => handleStyleMatchSelect('Yes')} className="w-full p-4 bg-green-100 rounded-lg hover:bg-green-200 transition-colors">Yes, it's a perfect match!</button>
        <button onClick={() => handleStyleMatchSelect('Almost')} className="w-full p-4 bg-yellow-100 rounded-lg hover:bg-yellow-200 transition-colors">Almost, but something is a little off.</button>
        <button onClick={() => handleStyleMatchSelect('No')} className="w-full p-4 bg-red-100 rounded-lg hover:bg-red-200 transition-colors">No, this doesn't feel like my style.</button>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="text-center">
      <Smile className="h-12 w-12 text-green-500 mx-auto mb-4" />
      <h3 className="text-xl font-bold text-gray-800 mb-2">Would you recommend us to a friend?</h3>
      <div className="flex justify-center gap-4 mt-4">
        <button onClick={() => handleRecommendationSelect(true)} className="p-4 bg-green-100 rounded-lg hover:bg-green-200 transition-colors"><ThumbsUp className="inline mr-2"/> Yes</button>
        <button onClick={() => handleRecommendationSelect(false)} className="p-4 bg-red-100 rounded-lg hover:bg-red-200 transition-colors"><ThumbsDown className="inline mr-2"/> No</button>
      </div>
      <textarea
        placeholder="Have more to say? We're listening..."
        value={feedbackData.additionalThoughts}
        onChange={(e) => setFeedbackData(prev => ({ ...prev, additionalThoughts: e.target.value }))}
        className="w-full mt-4 p-2 border rounded-lg"
      />
      <button onClick={handleSubmit} disabled={isSubmitting} className="mt-4 w-full bg-purple-600 text-white py-3 px-6 rounded-lg hover:bg-purple-700 transition-colors">
        {isSubmitting ? 'Sending...' : 'Submit Feedback'}
      </button>
    </div>
  );

  const renderSuccess = () => (
    <div className="text-center py-8">
      <div className="mb-6">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Heart className="h-8 w-8 text-green-600 fill-current" />
        </div>
        <h3 className="text-2xl font-bold text-gray-800 mb-2">
          Thank you! 💖
        </h3>
        <p className="text-gray-600">
          Your feedback helps our AI stylist get smarter!
        </p>
        <p className="text-sm text-purple-600 mt-2">
          Your next recommendations will be 10% better
        </p>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-purple-900/50 to-pink-900/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gradient-to-br from-white to-purple-50/30 rounded-3xl shadow-2xl max-w-md w-full transform transition-all duration-500 ease-out border border-purple-200/30">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-purple-100/50">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center shadow-lg">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-gray-800 text-lg">💜 Style Insights</span>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-purple-100 rounded-full transition-all duration-200 group"
          >
            <X className="h-5 w-5 text-gray-500 group-hover:text-purple-600" />
          </button>
        </div>

        {/* Progress Bar */}
        {!isSubmitted && (
          <div className="px-6 py-4">
            <div className="w-full bg-purple-100 rounded-full h-3 shadow-inner">
              <div 
                className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full transition-all duration-500 shadow-sm"
                style={{ width: `${(currentStep / 4) * 100}%` }}
              />
            </div>
            <div className="text-center mt-2 text-sm text-purple-600 font-medium">
              Step {currentStep} of 4
            </div>
          </div>
        )}

        {/* Content */}
        <div className="p-6">
          {isSubmitted ? renderSuccess() : (
            <>
              {currentStep === 1 && renderStep1()}
              {currentStep === 2 && renderStep2()}
              {currentStep === 3 && renderStep3()}
              {currentStep === 4 && renderStep4()}
            </>
          )}
        </div>

        {/* Footer */}
        {!isSubmitted && (
          <div className="px-6 pb-4">
            <div className="flex items-center justify-center space-x-1 text-xs text-purple-500/70">
              <Sparkles className="h-3 w-3" />
              <span>Powered by AI Fashion Intelligence</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FeedbackPopup;
