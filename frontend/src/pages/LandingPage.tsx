// import React from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { 
  ArrowRight, 
  Sparkle, 
  Camera, 
  ShoppingBag, 
  Instagram,
  Twitter,
  Linkedin,
  Facebook,
  Mail,
  Star,
  Palette,
  Zap
} from 'lucide-react';

const features = [
  {
    icon: Palette,
    title: "Color Theory Analysis",
    description: "Get personalized color suggestions based on advanced color theory and your unique skin tone."
  },
  {
    icon: ShoppingBag,
    title: "Smart Recommendations",
    description: "Receive tailored product suggestions that perfectly complement your natural coloring."
  },
  {
    icon: Camera,
    title: "Virtual Try-On",
    description: "Visualize how different colors look on you before making purchasing decisions."
  },
  {
    icon: Star,
    title: "Personalized Experience",
    description: "Enjoy a custom-tailored fashion journey designed specifically for your unique features."
  }
];

const testimonials = [
  {
    quote: "HueMatch completely transformed my shopping experience. I now know exactly which colors work best for me!",
    author: "Sarah J.",
    role: "Fashion Enthusiast"
  },
  {
    quote: "As a makeup artist, I recommend HueMatch to all my clients. The color recommendations are spot-on!",
    author: "Michael T.",
    role: "Professional Makeup Artist"
  },
  {
    quote: "I've saved so much money by avoiding colors that don't flatter me. This app is a game-changer!",
    author: "Emma R.",
    role: "Style Blogger"
  }
];

const galleryImages = [
  {
    url: "https://images.pexels.com/photos/2253832/pexels-photo-2253832.jpeg?auto=compress&cs=tinysrgb&w=600",
    alt: "Makeup Application"
  },
  {
    url: "https://images.pexels.com/photos/2113855/pexels-photo-2113855.jpeg?auto=compress&cs=tinysrgb&w=600",
    alt: "Foundation and Beauty Products"
  },
  {
    url: "https://images.pexels.com/photos/3373716/pexels-photo-3373716.jpeg?auto=compress&cs=tinysrgb&w=600",
    alt: "Colorful Makeup Palette"
  }
];

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-100 via-pink-50 to-white">
      <Navbar />
      
      {/* Hero Section */}
      <div className="relative pt-20 overflow-hidden">
        <div className="absolute top-0 right-0 w-1/2 h-1/2 bg-gradient-to-b from-purple-200 to-transparent opacity-30 blur-3xl"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-12">
            <div className="lg:w-1/2 space-y-8 relative">
              <div className="absolute -left-20 -top-20 w-40 h-40 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
              <div className="absolute -right-20 -bottom-20 w-40 h-40 bg-pink-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
              <h1 className="text-6xl lg:text-7xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600 leading-tight">
                Discover Your Perfect Colors
              </h1>
              <p className="text-xl text-gray-600 max-w-xl relative">
                Unlock your personal color palette with AI-powered analysis that enhances your natural beauty
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/demo"
                  className="group inline-flex items-center justify-center px-8 py-4 text-base font-medium rounded-full text-white bg-gradient-to-r from-purple-600 to-pink-600 hover:opacity-90 transition-all duration-300 shadow-lg hover:shadow-xl"
                >
                  Try Live Demo
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <button className="inline-flex items-center justify-center px-8 py-4 text-base font-medium rounded-full text-purple-600 bg-white/80 backdrop-blur hover:bg-white transition-all duration-300 shadow-md hover:shadow-lg border border-purple-100">
                  Learn More
                </button>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Zap className="h-4 w-4 text-pink-500" />
                <span>Join over 100,000 users who've found their perfect colors</span>
              </div>
            </div>
            
            <div className="lg:w-1/2 relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-200 to-pink-200 rounded-[2rem] blur-2xl opacity-30 transform rotate-6"></div>
              <div className="relative bg-white/50 backdrop-blur-sm p-4 rounded-[2rem] shadow-xl">
                <img
                  src="https://images.pexels.com/photos/2065195/pexels-photo-2065195.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"
                  alt="Woman applying makeup"
                  className="rounded-2xl shadow-lg w-full h-[400px] object-cover"
                />
                <div className="absolute -bottom-6 -right-6 bg-white rounded-2xl shadow-lg p-4 flex items-center gap-3">
                  <div className="p-2 bg-purple-50 rounded-lg">
                    <Sparkle className="h-6 w-6 text-pink-500" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">AI-Powered Beauty Analysis</span>
                </div>
              </div>
              
              {/* Small floating images */}
              <div className="absolute -top-10 -left-10 w-32 h-32 rounded-lg shadow-lg overflow-hidden border-4 border-white rotate-6">
                <img 
                  src="https://images.pexels.com/photos/2533266/pexels-photo-2533266.jpeg?auto=compress&cs=tinysrgb&w=200" 
                  alt="Foundation swatches" 
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="absolute -bottom-8 left-20 w-40 h-40 rounded-lg shadow-lg overflow-hidden border-4 border-white -rotate-3">
                <img 
                  src="https://images.pexels.com/photos/2537930/pexels-photo-2537930.jpeg?auto=compress&cs=tinysrgb&w=200" 
                  alt="Makeup products" 
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <section className="py-12 bg-white/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div className="p-6">
              <p className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">100K+</p>
              <p className="text-gray-600 mt-2">Active Users</p>
            </div>
            <div className="p-6">
              <p className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">12</p>
              <p className="text-gray-600 mt-2">Color Seasons</p>
            </div>
            <div className="p-6">
              <p className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">98%</p>
              <p className="text-gray-600 mt-2">Satisfaction Rate</p>
            </div>
            <div className="p-6">
              <p className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">5M+</p>
              <p className="text-gray-600 mt-2">Color Analyses</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <h2 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">
              Transform Your Style Journey
            </h2>
            <p className="mt-4 text-xl text-gray-600 max-w-3xl mx-auto">
              Discover how our AI-powered color analysis can elevate your fashion and beauty choices
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div 
                key={feature.title} 
                className="group bg-white/80 backdrop-blur rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 border border-purple-50 hover:border-pink-200"
                style={{ animationDelay: `${index * 150}ms` }}
              >
                <div className="p-3 bg-gradient-to-br from-purple-100 to-pink-100 rounded-xl w-fit mb-6 group-hover:scale-110 transition-transform">
                  <feature.icon className="h-8 w-8 text-pink-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gradient-to-r from-purple-50 to-pink-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900">
              How It Works
            </h2>
            <p className="mt-4 text-xl text-gray-600 max-w-3xl mx-auto">
              Get your personalized color palette in three simple steps
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white rounded-xl p-8 shadow-lg text-center relative overflow-hidden group hover:shadow-xl transition-all">
              <div className="absolute top-0 right-0 w-24 h-24 bg-purple-100 rounded-bl-full -mr-12 -mt-12 group-hover:bg-pink-100 transition-colors"></div>
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-6 text-white">
                <span className="text-2xl font-bold">1</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Upload Your Photo
              </h3>
              <p className="text-gray-600">
                Take a selfie or upload a photo in natural lighting to analyze your unique skin tone
              </p>
            </div>

            <div className="bg-white rounded-xl p-8 shadow-lg text-center relative overflow-hidden group hover:shadow-xl transition-all">
              <div className="absolute top-0 right-0 w-24 h-24 bg-purple-100 rounded-bl-full -mr-12 -mt-12 group-hover:bg-pink-100 transition-colors"></div>
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-6 text-white">
                <span className="text-2xl font-bold">2</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                AI Analysis
              </h3>
              <p className="text-gray-600">
                Our advanced AI analyzes your skin tone, undertones, and features to determine your color season
              </p>
            </div>

            <div className="bg-white rounded-xl p-8 shadow-lg text-center relative overflow-hidden group hover:shadow-xl transition-all">
              <div className="absolute top-0 right-0 w-24 h-24 bg-purple-100 rounded-bl-full -mr-12 -mt-12 group-hover:bg-pink-100 transition-colors"></div>
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-6 text-white">
                <span className="text-2xl font-bold">3</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Get Your Color Palette
              </h3>
              <p className="text-gray-600">
                Receive a personalized color palette with flattering colors for clothing, makeup, and accessories
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900">
              What Our Users Say
            </h2>
            <p className="mt-4 text-xl text-gray-600 max-w-3xl mx-auto">
              Join thousands of satisfied users who've transformed their style with HueMatch
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-white rounded-xl p-8 shadow-lg relative">
                <div className="absolute top-0 right-0 transform -translate-y-1/3 translate-x-1/3">
                  <div className="text-pink-100 text-8xl">"</div>
                </div>
                <p className="text-gray-600 mb-6 relative z-10">{testimonial.quote}</p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
                    {testimonial.author.charAt(0)}
                  </div>
                  <div className="ml-4">
                    <p className="font-medium text-gray-900">{testimonial.author}</p>
                    <p className="text-sm text-gray-500">{testimonial.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Gallery Section */}
      <section className="py-20 bg-gradient-to-r from-purple-50 to-pink-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900">
              See It in Action
            </h2>
            <p className="mt-4 text-xl text-gray-600 max-w-3xl mx-auto">
              Discover how HueMatch transforms the way you approach color
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {galleryImages.map((image, index) => (
              <div key={index} className="relative group overflow-hidden rounded-xl shadow-lg">
                <img
                  src={image.url}
                  alt={image.alt}
                  className="w-full h-80 object-cover transform group-hover:scale-110 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <div className="absolute bottom-6 left-6 text-white">
                    <p className="font-medium text-lg">{image.alt}</p>
                    <div className="w-10 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mt-2"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-3xl shadow-xl overflow-hidden">
            <div className="px-8 py-16 md:p-16 text-center text-white">
              <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to Discover Your Perfect Colors?</h2>
              <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
                Join thousands of users who have transformed their style with personalized color analysis
              </p>
              <Link
                to="/demo"
                className="inline-flex items-center justify-center px-8 py-4 text-base font-medium rounded-full text-purple-600 bg-white hover:bg-purple-50 transition-all duration-300 shadow-lg hover:shadow-xl"
              >
                Try Free Demo
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-6">
                <Sparkle className="h-6 w-6 text-pink-400" />
                <span className="text-xl font-bold">HueMatch</span>
              </div>
              <p className="text-gray-400">
                Transforming personal style with AI-powered color analysis technology
              </p>
            </div>

            <div>
              <h4 className="text-lg font-semibold mb-4">Company</h4>
              <ul className="space-y-2">
                <li><a href="#about" className="text-gray-400 hover:text-pink-400 transition-colors">About</a></li>
                <li><a href="#careers" className="text-gray-400 hover:text-pink-400 transition-colors">Careers</a></li>
                <li><a href="#press" className="text-gray-400 hover:text-pink-400 transition-colors">Press</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-lg font-semibold mb-4">Resources</h4>
              <ul className="space-y-2">
                <li><a href="#blog" className="text-gray-400 hover:text-pink-400 transition-colors">Blog</a></li>
                <li><a href="#documentation" className="text-gray-400 hover:text-pink-400 transition-colors">Documentation</a></li>
                <li><a href="#support" className="text-gray-400 hover:text-pink-400 transition-colors">Support</a></li>
              </ul>
            </div>

            <div>
              <h4 className="text-lg font-semibold mb-4">Connect</h4>
              <div className="flex space-x-4">
                <a href="#twitter" className="text-gray-400 hover:text-pink-400 transition-colors">
                  <Twitter className="h-6 w-6" />
                </a>
                <a href="#linkedin" className="text-gray-400 hover:text-pink-400 transition-colors">
                  <Linkedin className="h-6 w-6" />
                </a>
                <a href="#facebook" className="text-gray-400 hover:text-pink-400 transition-colors">
                  <Facebook className="h-6 w-6" />
                </a>
                <a href="#instagram" className="text-gray-400 hover:text-pink-400 transition-colors">
                  <Instagram className="h-6 w-6" />
                </a>
                <a href="#contact" className="text-gray-400 hover:text-pink-400 transition-colors">
                  <Mail className="h-6 w-6" />
                </a>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-400">
            <p>© 2023 HueMatch. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;