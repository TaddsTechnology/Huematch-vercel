import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import ImageCapture from '../components/ImageCapture';
import { Camera, Shield, Image, RefreshCw } from 'lucide-react';
import { Client } from "@gradio/client";

// Add interface at the top of the file
interface SkinAnalysisResult {
  monk_skin_tone: string;
  monk_hex: string;
  derived_hex_code: string;
  dominant_rgb: number[];
}

const DemoProcess = () => {
  const navigate = useNavigate();
  const [isProcessing, setIsProcessing] = useState(false);
  const [skinAnalysisResult, setSkinAnalysisResult] = useState<SkinAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  const analyzeSkinColor = async (imageBlob: Blob) => {
    try {
      // Connect to Gradio model repository
      const client = await Client.connect("davelop/face_skin_color");
      
      // Call the predict endpoint
      const prediction = await client.predict("/predict", { 
        image_path: imageBlob 
      });
      
      setSkinAnalysisResult(prediction.data as SkinAnalysisResult);
      console.log("Skin analysis result:", prediction.data);
      
      // Store the result in sessionStorage for use in other components
      sessionStorage.setItem('skinAnalysis', JSON.stringify(prediction.data));
      
      // Continue with navigation after analysis
      navigate('/demo/try-on');
    } catch (error) {
      console.error("Skin analysis error:", error);
      // Handle error appropriately
      setCameraError("Failed to analyze skin color. Please try again.");
    }
  };

  const handleImageCapture = async (image: string) => {
    setIsProcessing(true);
    setIsAnalyzing(true);

    try {
      // Store the captured image in sessionStorage
      sessionStorage.setItem('capturedImage', image);
      
      // Convert base64 image to blob
      const response = await fetch(image);
      const blob = await response.blob();
      
      // Analyze skin color
      await analyzeSkinColor(blob);
    } catch (error) {
      console.error("Image processing error:", error);
      setCameraError("Failed to process image. Please try again.");
    } finally {
      setIsProcessing(false);
      setIsAnalyzing(false);
    }
  };

  return (
    <Layout>
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
        {/* Hero Section with Animation */}
        <div className="max-w-6xl mx-auto px-4 py-16">
          <div className="text-center mb-16 animate-fadeIn">
            <h1 className="text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Find Your Perfect 
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-pink-600">
                {" "}Color Match
              </span>
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
              Our AI-powered tool analyzes your skin tone to create your personalized color palette
            </p>
          </div>

          {/* Main Content Grid */}
          <div className="grid md:grid-cols-2 gap-12 items-start mb-20">
            {/* Left Column - Image Capture */}
            <div className="space-y-6">
              <div className="bg-white rounded-3xl shadow-xl p-8 transition-all duration-300 hover:shadow-2xl">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                  Take or Upload Photo
                </h2>
                
                {cameraError && (
                  <div className="bg-red-50 text-red-600 p-4 rounded-xl mb-6 flex items-center">
                    <Shield className="w-5 h-5 mr-2" />
                    <p>{cameraError}</p>
                  </div>
                )}

                {isProcessing ? (
                  <div className="text-center py-12">
                    <RefreshCw className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-4" />
                    <p className="text-lg font-medium text-gray-700">Processing your image...</p>
                    <p className="text-gray-500">This will only take a moment</p>
                  </div>
                ) : (
                  <ImageCapture onImageCapture={handleImageCapture} />
                )}
              </div>

              {/* Quick Tips */}
              <div className="bg-gradient-to-br from-purple-100 to-pink-100 rounded-3xl p-8">
                <div className="flex items-center mb-4">
                  <Camera className="w-6 h-6 text-purple-600 mr-2" />
                  <h3 className="text-lg font-semibold text-gray-900">Quick Tips</h3>
                </div>
                <ul className="space-y-3 text-gray-700">
                  <li className="flex items-center">
                    <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mr-2" />
                    Use natural lighting
                  </li>
                  <li className="flex items-center">
                    <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mr-2" />
                    Face the camera directly
                  </li>
                  <li className="flex items-center">
                    <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mr-2" />
                    Remove glasses if wearing
                  </li>
                </ul>
              </div>
            </div>

            {/* Right Column - Process Steps */}
            <div className="space-y-6">
              <div className="bg-white rounded-3xl shadow-lg p-8">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6">
                  How It Works
                </h2>
                <div className="space-y-8">
                  {[
                    {
                      icon: <Camera className="w-8 h-8 text-purple-500" />,
                      title: "Capture",
                      description: "Take a clear photo of your face in good lighting"
                    },
                    {
                      icon: <RefreshCw className="w-8 h-8 text-purple-500" />,
                      title: "Analysis",
                      description: "Our AI analyzes your unique skin tone"
                    },
                    {
                      icon: <Image className="w-8 h-8 text-purple-500" />,
                      title: "Results",
                      description: "Get your personalized color recommendations"
                    }
                  ].map((step, index) => (
                    <div key={index} className="flex items-start">
                      <div className="bg-purple-50 p-3 rounded-xl mr-4">
                        {step.icon}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-1">
                          {step.title}
                        </h3>
                        <p className="text-gray-600">{step.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Loading Overlay */}
        {isAnalyzing && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
            <div className="bg-white rounded-3xl p-8 max-w-md w-full mx-4 shadow-2xl animate-fadeIn">
              <RefreshCw className="w-12 h-12 text-purple-500 animate-spin mx-auto mb-6" />
              <h3 className="text-2xl font-semibold text-gray-900 mb-2 text-center">
                Analyzing your skin tone
              </h3>
              <p className="text-gray-600 text-center">
                Our AI is working its magic to find your perfect color matches
              </p>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default DemoProcess;