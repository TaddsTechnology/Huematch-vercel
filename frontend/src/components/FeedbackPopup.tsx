import React, { useState } from 'react';
import { X, Heart, Meh, Frown, Send, MessageCircle, Star } from 'lucide-react';

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
  emotion: string;
  rating: number;
  issues: string[];
  improvements: string;
  wouldRecommend: boolean;
}

const FeedbackPopup: React.FC<FeedbackPopupProps> = ({ 
  isVisible, 
  onClose, 
  userContext = {} 
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [feedbackData, setFeedbackData] = useState<FeedbackData>({
    emotion: '',
    rating: 0,
    issues: [],
    improvements: '',
    wouldRecommend: false
  });

  if (!isVisible) return null;

  const handleEmotionSelect = (emotion: string) => {
    setFeedbackData(prev => ({ ...prev, emotion }));
    
    // If positive emotion, skip to final step
    if (emotion === 'love' || emotion === 'like') {
      setCurrentStep(4);
    } else {
      setCurrentStep(2);
    }
  };

  const handleRatingSelect = (rating: number) => {
    setFeedbackData(prev => ({ ...prev, rating }));
    setCurrentStep(3);
  };

  const handleIssueToggle = (issue: string) => {
    setFeedbackData(prev => ({
      ...prev,
      issues: prev.issues.includes(issue)
        ? prev.issues.filter(i => i !== issue)
        : [...prev.issues, issue]
    }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    try {
      const payload = {
        ...feedbackData,
        userContext,
        timestamp: new Date().toISOString(),
        page: 'recommendations'
      };

      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setIsSubmitted(true);
        setTimeout(() => {
          onClose();
          // Reset state after animation
          setTimeout(() => {
            setCurrentStep(1);
            setIsSubmitted(false);
            setFeedbackData({
              emotion: '',
              rating: 0,
              issues: [],
              improvements: '',
              wouldRecommend: false
            });
          }, 300);
        }, 2000);
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStep1 = () => (
    <div className="text-center">
      <div className="mb-6">
        <MessageCircle className="h-12 w-12 text-purple-600 mx-auto mb-4" />
        <h3 className="text-xl font-bold text-gray-800 mb-2">
          How do you feel about these recommendations?
        </h3>
        <p className="text-gray-600 text-sm">
          Your feedback helps our AI stylist learn your preferences
        </p>
      </div>
      
      <div className="space-y-3">
        <button
          onClick={() => handleEmotionSelect('love')}
          className="w-full flex items-center justify-center space-x-3 p-4 rounded-lg border-2 border-transparent hover:border-purple-300 hover:bg-purple-50 transition-all duration-200 group"
        >
          <div className="text-2xl">😍</div>
          <span className="font-medium text-gray-700 group-hover:text-purple-700">Love them!</span>
        </button>
        
        <button
          onClick={() => handleEmotionSelect('like')}
          className="w-full flex items-center justify-center space-x-3 p-4 rounded-lg border-2 border-transparent hover:border-purple-300 hover:bg-purple-50 transition-all duration-200 group"
        >
          <div className="text-2xl">😊</div>
          <span className="font-medium text-gray-700 group-hover:text-purple-700">Pretty good</span>
        </button>
        
        <button
          onClick={() => handleEmotionSelect('okay')}
          className="w-full flex items-center justify-center space-x-3 p-4 rounded-lg border-2 border-transparent hover:border-purple-300 hover:bg-purple-50 transition-all duration-200 group"
        >
          <div className="text-2xl">😐</div>
          <span className="font-medium text-gray-700 group-hover:text-purple-700">Okay</span>
        </button>
        
        <button
          onClick={() => handleEmotionSelect('not-great')}
          className="w-full flex items-center justify-center space-x-3 p-4 rounded-lg border-2 border-transparent hover:border-purple-300 hover:bg-purple-50 transition-all duration-200 group"
        >
          <div className="text-2xl">😕</div>
          <span className="font-medium text-gray-700 group-hover:text-purple-700">Not great</span>
        </button>
        
        <button
          onClick={() => handleEmotionSelect('dislike')}
          className="w-full flex items-center justify-center space-x-3 p-4 rounded-lg border-2 border-transparent hover:border-purple-300 hover:bg-purple-50 transition-all duration-200 group"
        >
          <div className="text-2xl">😞</div>
          <span className="font-medium text-gray-700 group-hover:text-purple-700">Don't like them</span>
        </button>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="text-center">
      <div className="mb-6">
        <Star className="h-12 w-12 text-purple-600 mx-auto mb-4" />
        <h3 className="text-xl font-bold text-gray-800 mb-2">
          How would you rate the accuracy?
        </h3>
        <p className="text-gray-600 text-sm">
          On a scale of 1-5, how well did we match your style?
        </p>
      </div>
      
      <div className="flex justify-center space-x-2 mb-6">
        {[1, 2, 3, 4, 5].map((rating) => (
          <button
            key={rating}
            onClick={() => handleRatingSelect(rating)}
            className="p-2 rounded-lg hover:bg-purple-50 transition-colors duration-200"
          >
            <Star 
              className={`h-8 w-8 ${
                rating <= feedbackData.rating 
                  ? 'text-yellow-400 fill-current' 
                  : 'text-gray-300'
              }`} 
            />
          </button>
        ))}
      </div>
    </div>
  );

  const renderStep3 = () => {
    const issueOptions = [
      'More variety in colors',
      'Different price ranges',
      'More styles/brands',
      'Better size options',
      'More trendy items',
      'Classic/timeless pieces',
      'Better quality items',
      'More sustainable options'
    ];

    return (
      <div className="text-center">
        <div className="mb-6">
          <MessageCircle className="h-12 w-12 text-purple-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-800 mb-2">
            What could we improve?
          </h3>
          <p className="text-gray-600 text-sm">
            Select all that apply (optional)
          </p>
        </div>
        
        <div className="grid grid-cols-2 gap-2 mb-6">
          {issueOptions.map((issue) => (
            <button
              key={issue}
              onClick={() => handleIssueToggle(issue)}
              className={`p-3 text-sm rounded-lg border-2 transition-all duration-200 ${
                feedbackData.issues.includes(issue)
                  ? 'border-purple-500 bg-purple-50 text-purple-700'
                  : 'border-gray-200 hover:border-purple-300 hover:bg-purple-50'
              }`}
            >
              {issue}
            </button>
          ))}
        </div>
        
        <button
          onClick={() => setCurrentStep(4)}
          className="w-full bg-purple-600 text-white py-3 px-6 rounded-lg hover:bg-purple-700 transition-colors duration-200 font-medium"
        >
          Continue
        </button>
      </div>
    );
  };

  const renderStep4 = () => (
    <div className="text-center">
      <div className="mb-6">
        <Heart className="h-12 w-12 text-purple-600 mx-auto mb-4" />
        <h3 className="text-xl font-bold text-gray-800 mb-2">
          One final question!
        </h3>
        <p className="text-gray-600 text-sm mb-4">
          Anything else we should know?
        </p>
        
        <textarea
          placeholder="Tell us more about your style preferences... (optional)"
          value={feedbackData.improvements}
          onChange={(e) => setFeedbackData(prev => ({ ...prev, improvements: e.target.value }))}
          className="w-full p-3 border border-gray-200 rounded-lg resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          rows={3}
        />
      </div>
      
      <div className="space-y-3">
        <div className="flex items-center justify-center space-x-4 mb-4">
          <span className="text-gray-700">Would you recommend our AI stylist?</span>
          <div className="flex space-x-2">
            <button
              onClick={() => setFeedbackData(prev => ({ ...prev, wouldRecommend: true }))}
              className={`px-4 py-2 rounded-lg transition-colors duration-200 ${
                feedbackData.wouldRecommend 
                  ? 'bg-green-500 text-white' 
                  : 'bg-gray-200 hover:bg-green-100'
              }`}
            >
              Yes
            </button>
            <button
              onClick={() => setFeedbackData(prev => ({ ...prev, wouldRecommend: false }))}
              className={`px-4 py-2 rounded-lg transition-colors duration-200 ${
                !feedbackData.wouldRecommend && feedbackData.wouldRecommend !== null
                  ? 'bg-red-500 text-white' 
                  : 'bg-gray-200 hover:bg-red-100'
              }`}
            >
              No
            </button>
          </div>
        </div>
        
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="w-full bg-purple-600 text-white py-3 px-6 rounded-lg hover:bg-purple-700 transition-colors duration-200 font-medium flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              <span>Sending...</span>
            </>
          ) : (
            <>
              <Send className="h-4 w-4" />
              <span>Send Feedback</span>
            </>
          )}
        </button>
      </div>
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto transform transition-all duration-300 ease-out">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
              <MessageCircle className="h-4 w-4 text-purple-600" />
            </div>
            <span className="font-medium text-gray-800">Quick Style Check</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors duration-200"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Progress Bar */}
        {!isSubmitted && (
          <div className="px-6 py-2">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(currentStep / 4) * 100}%` }}
              />
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
            <div className="flex items-center justify-center space-x-1 text-xs text-gray-500">
              <span>Powered by</span>
              <span className="font-medium text-purple-600">AI Fashion</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FeedbackPopup;
