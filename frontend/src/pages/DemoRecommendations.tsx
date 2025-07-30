import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { Star, Sparkles, Crown, Shirt, Palette } from 'lucide-react';
import ProductRecommendations from '../components/ProductRecommendations';
import FeedbackPopup from '../components/FeedbackPopup';
import { API_ENDPOINTS, buildApiUrl } from '../config/api';
import { monkSkinTones } from '../lib/data/monkSkinTones';

// Consolidated interfaces
interface Product {
  id?: number;
  brand: string;
  name: string;
  price: string;
  rating: number;
  image: string;
  image_url: string;
  mst: string;
  desc: string;
  product_type?: string;
} 

interface SkinAnalysisResult {
  label: string;
  confidences: null;
  monk_skin_tone?: string;
  seasonal_type?: string;
}

interface ApiProduct {
  product?: string;
  name?: string;
  brand?: string;
  Brand?: string;
  Product_Name?: string;
  "Product Name"?: string;
  Price?: string;
  Image_URL?: string;
  "Image URL"?: string;
  imgSrc?: string;
  image?: string;
  image_url?: string;
  product_name?: string;
  price?: string;
  rating?: number;
  mst: string;
  desc: string;
  imgAlt: string;
  gender: string;
  masterCategory: string;
  subCategory: string;
  baseColour: string;
  usage: string;
  season: string;
  product_type?: string;
}

interface ColorInfo {
  name: string;
  hex: string;
}

interface ColorRecommendations {
  colors_that_suit: ColorInfo[];
  seasonal_type?: string;
  monk_skin_tone?: string;
  message?: string;
}

const DemoRecommendations = () => {
  const [showFeedbackPopup, setShowFeedbackPopup] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowFeedbackPopup(true);
    }, 4000); // Show popup after 4 seconds

    return () => clearTimeout(timer);
  }, []);

  const handleFeedbackClose = () => {
    setShowFeedbackPopup(false);
  };
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [skinAnalysis, setSkinAnalysis] = useState<SkinAnalysisResult | null>(null);
  const [skinHex, setSkinHex] = useState<string>('#d7bd96'); // Default skin hex
  const [monkSkinTone, setMonkSkinTone] = useState<string>('Monk05'); // Default Monk skin tone
  const [activeTab, setActiveTab] = useState<'makeup' | 'outfit' | 'colors' | 'products'>('makeup');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [availableFilters, setAvailableFilters] = useState<{[key: string]: string[]}>({});
  const [selectedFilters, setSelectedFilters] = useState<{[key: string]: string}>({});
  const [colorRecommendations, setColorRecommendations] = useState<ColorRecommendations | null>(null);
  const itemsPerPage = 24;

  // Handle page changes
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Handle filter changes
  const handleFilterChange = (filters: {[key: string]: string}) => {
    setSelectedFilters(filters);
    setCurrentPage(1);
  };

  // Display error message if needed
  const displayError = () => {
    if (error) {
      return (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      );
    }
    return null;
  };

  // Fetch color recommendations with enhanced error handling and fallbacks
  useEffect(() => {
    const fetchColorRecommendations = async () => {
      if (activeTab === 'colors' && (skinHex || monkSkinTone)) {
        try {
          console.log('Fetching color recommendations for:', { skinHex, monkSkinTone });
          
          // Build query parameters
          const queryParams = new URLSearchParams();
          
          // Add hex color if available (clean format)
          if (skinHex) {
            const cleanHex = skinHex.startsWith('#') ? skinHex.substring(1) : skinHex;
            queryParams.append('hex_color', cleanHex);
          }
          
          // Add Monk skin tone if available
          if (monkSkinTone) {
            queryParams.append('skin_tone', monkSkinTone);
          }
          
          console.log('API request parameters:', Object.fromEntries(queryParams));
          
          // Try enhanced color recommendations API first
          let response = await fetch(buildApiUrl(API_ENDPOINTS.COLOR_RECOMMENDATIONS, Object.fromEntries(queryParams)));
          
          if (response.ok) {
            const data = await response.json();
            console.log('Color recommendations response:', data);
            setColorRecommendations(data);
            setError(null); // Clear any previous errors
          } else {
            console.error('Color matching service temporarily unavailable:', response.status);
            
            // Try the color library as fallback
            try {
              const fallbackResponse = await fetch(buildApiUrl(API_ENDPOINTS.COLOR_PALETTES_DB, Object.fromEntries(queryParams)));
              if (fallbackResponse.ok) {
                const fallbackData = await fallbackResponse.json();
                console.log('Using color library for recommendations:', fallbackData);
                setColorRecommendations(fallbackData);
                setError(null);
              } else {
                throw new Error('Color services temporarily unavailable');
              }
            } catch (fallbackError) {
              console.error('Color library also unavailable:', fallbackError);
              // Use local color matching as final fallback
              const localRecommendations = getLocalColorRecommendations(skinHex, monkSkinTone);
              setColorRecommendations(localRecommendations);
            }
          }
        } catch (err) {
          console.error('Unable to fetch color recommendations:', err);
          // Use local color matching as fallback
          const localRecommendations = getLocalColorRecommendations(skinHex, monkSkinTone);
          setColorRecommendations(localRecommendations);
        }
      }
    };

    fetchColorRecommendations();
  }, [activeTab, skinHex, monkSkinTone]);

  // Fetch products based on active tab
  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      setError(null);
      
      try {
        let response;
        let transformedProducts: Product[] = [];
        
        if (activeTab === 'makeup') {
          // Build query parameters for makeup products
          const queryParams = new URLSearchParams();
          queryParams.append('page', currentPage.toString());
          queryParams.append('limit', itemsPerPage.toString());
          
          // Add Monk skin tone for better product matching
          if (monkSkinTone) {
            queryParams.append('mst', monkSkinTone);
          }
          
          // Add hex color for color matching
          if (skinHex) {
            queryParams.append('ogcolor', skinHex.replace('#', ''));
          }
          
          // Add selected filters if any
          if (selectedFilters.productType) {
            queryParams.append('product_type', selectedFilters.productType);
          }
          
          console.log(`Fetching makeup products with params: ${queryParams.toString()}`);
          response = await fetch(buildApiUrl(API_ENDPOINTS.MAKEUP_DATA, Object.fromEntries(queryParams)));
          
          if (!response.ok) {
            throw new Error(`Unable to load makeup recommendations: ${response.status} ${response.statusText}`);
          }

          const data = await response.json();
          transformedProducts = data.data.map((item: ApiProduct) => ({
            id: Math.random(),
            name: item.product_name || item.Product_Name || item.name || '',
            brand: item.brand || item.Brand || 'Unknown',
            price: item.price || item.Price || '$29.99',
            rating: item.rating || 4.5,
            image: item.imgSrc || item.image_url || item.Image_URL || item.image || '',
            image_url: item.imgSrc || item.image_url || item.Image_URL || item.image || '',
            mst: item.mst || '',
            desc: item.imgAlt || item.desc || '',
            product_type: item.product_type || ''
          }));

          setTotalItems(data.total_items || transformedProducts.length);
          setTotalPages(data.total_pages || Math.ceil(transformedProducts.length / itemsPerPage));
          
          // Fetch available makeup types for filtering
          if (Object.keys(availableFilters).length === 0) {
            try {
              const typesResponse = await fetch('http://localhost:8000/makeup-types');
              if (typesResponse.ok) {
                const typesData = await typesResponse.json();
                setAvailableFilters({
                  productType: typesData.types || []
                });
              }
            } catch (err) {
              console.error('Unable to load makeup categories:', err);
            }
          }
        } else if (activeTab === 'outfit') {
          // For outfit tab, use recommended colors if available
          const colorParams = new URLSearchParams();
          colorParams.append('page', currentPage.toString());
          colorParams.append('limit', itemsPerPage.toString());
          
          // Use color recommendations if available
          if (colorRecommendations && colorRecommendations.colors_that_suit && colorRecommendations.colors_that_suit.length > 0) {
            // Add up to 4 recommended colors if available
            const colorNames = colorRecommendations.colors_that_suit
              .slice(0, 4)
              .filter(color => color && color.name)
              .map(color => color.name);
              
            if (colorNames.length > 0) {
              colorNames.forEach(colorName => {
                colorParams.append('color', colorName);
              });
            } else {
              // Default colors if no valid names
              colorParams.append('color', 'Blue');
              colorParams.append('color', 'Black');
              colorParams.append('color', 'White');
              colorParams.append('color', 'Grey');
            }
          } else {
            // Default colors if no recommendations
            colorParams.append('color', 'Blue');
            colorParams.append('color', 'Black');
            colorParams.append('color', 'White');
            colorParams.append('color', 'Grey');
          }
          
          console.log(`Fetching outfits with params: ${colorParams.toString()}`);
          response = await fetch(`http://localhost:8000/apparel?${colorParams.toString()}`);
          
          if (!response.ok) {
            throw new Error(`Unable to load outfit recommendations: ${response.status} ${response.statusText}`);
          }

          const data = await response.json();
          
          if (data.error) {
            throw new Error(data.error);
          }
          
          transformedProducts = data.data.map((item: {
            'Product Name'?: string;
            'Price'?: string;
            'Image URL'?: string;
            'Product Type'?: string;
          }) => ({
            id: Math.random(),
            name: item['Product Name'] || '',
            brand: 'Apparel',
            price: item['Price'] || '$0.00',
            rating: 4.5,
            image: item['Image URL'] || '',
            image_url: item['Image URL'] || '',
            mst: '',
            desc: item['Product Type'] || '',
            product_type: item['Product Type'] || ''
          }));
          
          setTotalItems(data.total_items || transformedProducts.length);
          setTotalPages(data.total_pages || Math.ceil(transformedProducts.length / itemsPerPage));
        }

        setProducts(transformedProducts);
        setLoading(false);
      } catch (err) {
        console.error('Error:', err);
        // TODO: Uncomment when proper data is available
        // setError(err instanceof Error ? err.message : 'An error occurred');
        setLoading(false);
        setProducts([]); // Clear products on error
      }
    };

    fetchProducts();
  }, [navigate, activeTab, currentPage, selectedFilters, skinHex, monkSkinTone, colorRecommendations]);

  // Initialize skin tone and hex from session storage or use defaults
  useEffect(() => {
    try {
      const storedAnalysis = sessionStorage.getItem('skinAnalysis');
      if (storedAnalysis) {
        const analysisData = JSON.parse(storedAnalysis);
        
        // Handle both old array format and new object format
        if (Array.isArray(analysisData) && analysisData.length >= 2) {
          // Old format: [analysis, hex]
          setSkinAnalysis(analysisData[0]);
          setSkinHex(analysisData[1]);
          
          // Determine Monk skin tone from hex color
          const hexColor = analysisData[1];
          const monkId = determineMonkSkinTone(hexColor);
          setMonkSkinTone(monkId);
        } else if (analysisData && typeof analysisData === 'object' && analysisData.monk_skin_tone) {
          // New format: direct SkinAnalysisResult object
          setSkinAnalysis(analysisData);
          
          // Use the derived_hex_code or monk_hex as the primary skin hex
          const hexColor = analysisData.derived_hex_code || analysisData.monk_hex;
          setSkinHex(hexColor);
          setMonkSkinTone(analysisData.monk_skin_tone);
          
          console.log('Skin analysis result:', analysisData);
        }
      }
    } catch (err) {
      console.error('Unable to load your color profile from session storage:', err);
      setError('Unable to load your color profile. Please try analyzing your photo again.');
    }
  }, []);
  
  // Function to determine the closest Monk skin tone based on hex color
  const determineMonkSkinTone = (hexColor: string): string => {
    // Remove the # if present
    const hex = hexColor.startsWith('#') ? hexColor.substring(1) : hexColor;
    
    // Define the Monk skin tone hex values
    const monkHexValues = [
      { id: 'Monk01', hex: 'f6ede4' },
      { id: 'Monk02', hex: 'f3e7db' },
      { id: 'Monk03', hex: 'f7ead0' },
      { id: 'Monk04', hex: 'eadaba' },
      { id: 'Monk05', hex: 'd7bd96' },
      { id: 'Monk06', hex: 'a07e56' },
      { id: 'Monk07', hex: '825c43' },
      { id: 'Monk08', hex: '604134' },
      { id: 'Monk09', hex: '3a312a' },
      { id: 'Monk10', hex: '292420' }
    ];
    
    // Convert hex to RGB
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    
    // Find the closest match
    let closestMatch = monkHexValues[0];
    let minDistance = Number.MAX_VALUE;
    
    monkHexValues.forEach(monk => {
      const mr = parseInt(monk.hex.substring(0, 2), 16);
      const mg = parseInt(monk.hex.substring(2, 4), 16);
      const mb = parseInt(monk.hex.substring(4, 6), 16);
      
      // Calculate Euclidean distance in RGB space
      const distance = Math.sqrt(
        Math.pow(r - mr, 2) + 
        Math.pow(g - mg, 2) + 
        Math.pow(b - mb, 2)
      );
      
      if (distance < minDistance) {
        minDistance = distance;
        closestMatch = monk;
      }
    });
    
    return closestMatch.id;
  };

  // Local color recommendations function as fallback
  const getLocalColorRecommendations = (skinHex: string, monkSkinTone: string): ColorRecommendations => {
    // Enhanced color palettes based on Monk skin tone
    const colorPalettes: { [key: string]: ColorInfo[] } = {
      'Monk01': [
        { name: "Navy Blue", hex: "#003057" },
        { name: "Soft Pink", hex: "#F395C7" },
        { name: "Lavender", hex: "#A277A6" },
        { name: "Emerald", hex: "#009775" },
        { name: "Burgundy", hex: "#890C58" },
        { name: "Cobalt Blue", hex: "#0057B8" },
        { name: "Soft Coral", hex: "#F88379" },
        { name: "Powder Blue", hex: "#9BCBEB" }
      ],
      'Monk02': [
        { name: "Powder Blue", hex: "#9BCBEB" },
        { name: "Soft Plum", hex: "#86647A" },
        { name: "Dusty Rose", hex: "#D592AA" },
        { name: "Slate Blue", hex: "#57728B" },
        { name: "Soft Teal", hex: "#00B0B9" },
        { name: "Mauve", hex: "#C4A4A7" },
        { name: "Light Coral", hex: "#F08080" },
        { name: "Periwinkle", hex: "#CCCCFF" }
      ],
      'Monk03': [
        { name: "Peach", hex: "#FCC89B" },
        { name: "Mint", hex: "#A5DFD3" },
        { name: "Coral", hex: "#FF8D6D" },
        { name: "Light Yellow", hex: "#F5E1A4" },
        { name: "Aqua", hex: "#A4DBE8" },
        { name: "Soft Pink", hex: "#FAAA8D" },
        { name: "Apricot", hex: "#FBCEB1" },
        { name: "Sky Blue", hex: "#87CEEB" }
      ],
      'Monk04': [
        { name: "Warm Beige", hex: "#FDAA63" },
        { name: "Golden Yellow", hex: "#FFB81C" },
        { name: "Apricot", hex: "#FF8F1C" },
        { name: "Coral", hex: "#FFA38B" },
        { name: "Warm Green", hex: "#74AA50" },
        { name: "Turquoise", hex: "#2DCCD3" },
        { name: "Honey", hex: "#E6C200" },
        { name: "Warm Orange", hex: "#FF8C00" }
      ],
      'Monk05': [
        { name: "Turquoise", hex: "#008EAA" },
        { name: "Clear Yellow", hex: "#FFCD00" },
        { name: "Bright Coral", hex: "#FF8D6D" },
        { name: "Violet", hex: "#963CBD" },
        { name: "Bright Green", hex: "#00A499" },
        { name: "Watermelon", hex: "#E40046" },
        { name: "Amber", hex: "#FFBF00" },
        { name: "Royal Blue", hex: "#4169E1" }
      ],
      'Monk06': [
        { name: "Mustard", hex: "#B89D18" },
        { name: "Rust", hex: "#9D4815" },
        { name: "Olive", hex: "#A09958" },
        { name: "Burnt Orange", hex: "#C4622D" },
        { name: "Teal", hex: "#00778B" },
        { name: "Forest Green", hex: "#205C40" },
        { name: "Copper", hex: "#B87333" },
        { name: "Deep Gold", hex: "#B8860B" }
      ],
      'Monk07': [
        { name: "Burgundy", hex: "#890C58" },
        { name: "Chocolate", hex: "#5C462B" },
        { name: "Deep Teal", hex: "#00594C" },
        { name: "Rust", hex: "#9D4815" },
        { name: "Olive", hex: "#5E7E29" },
        { name: "Terracotta", hex: "#A6631B" },
        { name: "Forest Green", hex: "#228B22" },
        { name: "Bronze", hex: "#CD7F32" }
      ],
      'Monk08': [
        { name: "Hot Pink", hex: "#E3006D" },
        { name: "Cobalt Blue", hex: "#0057B8" },
        { name: "True Red", hex: "#CE0037" },
        { name: "Violet", hex: "#963CBD" },
        { name: "Emerald", hex: "#009775" },
        { name: "Gold", hex: "#FFB81C" },
        { name: "Royal Purple", hex: "#800080" },
        { name: "Bright Yellow", hex: "#FFCD00" }
      ],
      'Monk09': [
        { name: "Deep Claret", hex: "#890C58" },
        { name: "Forest Green", hex: "#00594C" },
        { name: "True Red", hex: "#CE0037" },
        { name: "Navy", hex: "#002D72" },
        { name: "Amethyst", hex: "#84329B" },
        { name: "White", hex: "#FEFEFE" },
        { name: "Silver", hex: "#C0C0C0" },
        { name: "Deep Purple", hex: "#301934" }
      ],
      'Monk10': [
        { name: "Hot Pink", hex: "#E3006D" },
        { name: "Cobalt Blue", hex: "#0057B8" },
        { name: "True Red", hex: "#CE0037" },
        { name: "Bright Yellow", hex: "#FFCD00" },
        { name: "Emerald", hex: "#009775" },
        { name: "White", hex: "#FEFEFE" },
        { name: "Electric Blue", hex: "#0000FF" },
        { name: "Bright Green", hex: "#66FF00" }
      ]
    };

    // Get colors for the current Monk skin tone, fallback to Monk05 if not found
    const colors = colorPalettes[monkSkinTone] || colorPalettes['Monk05'] || [
      { name: "Navy Blue", hex: "#000080" },
      { name: "Forest Green", hex: "#228B22" },
      { name: "Burgundy", hex: "#800020" },
      { name: "Charcoal Gray", hex: "#36454F" },
      { name: "Cream White", hex: "#F5F5DC" },
      { name: "Soft Pink", hex: "#FFB6C1" }
    ];

    // Map Monk skin tone to seasonal type
    const seasonalTypeMap: { [key: string]: string } = {
      'Monk01': 'Light Spring',
      'Monk02': 'Light Spring', 
      'Monk03': 'Clear Spring',
      'Monk04': 'Warm Spring',
      'Monk05': 'Soft Autumn',
      'Monk06': 'Warm Autumn',
      'Monk07': 'Deep Autumn',
      'Monk08': 'Deep Winter',
      'Monk09': 'Cool Winter',
      'Monk10': 'Clear Winter'
    };

    const seasonalType = seasonalTypeMap[monkSkinTone] || 'Universal';

    return {
      colors_that_suit: colors,
      seasonal_type: seasonalType,
      monk_skin_tone: monkSkinTone,
      message: "These color recommendations are based on your Monk skin tone analysis and seasonal color theory."
    };
  };

  return (
    <Layout>
      <div className="min-h-screen bg-gray-50">
        {/* Feedback Popup */}
        <FeedbackPopup 
          isVisible={showFeedbackPopup}
          onClose={handleFeedbackClose}
          userContext={{
            monkSkinTone,
            activeTab,
            sessionId: Date.now().toString() // Simple session ID
          }}
        />
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-20">
            <div className="text-center">
              {skinHex && (
                <div className="flex justify-center mb-6">
                  <div className="bg-white p-3 rounded-lg shadow-lg">
                    <div className="flex items-center space-x-3">
                      <div 
                        className="w-8 h-8 rounded-full border-2 border-white shadow-lg" 
                        style={{ backgroundColor: skinHex }}
                        title="Your Skin Tone"
                      />
                    </div>
                  </div>
                </div>
              )}
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
                Your Perfect Beauty Match
              </h1>
              <p className="mt-4 text-xl text-white max-w-2xl mx-auto">
                We've curated these products specifically for your skin tone
              </p>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-8 mt-8">
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => setActiveTab('makeup')}
              className={`px-6 py-2 rounded-lg flex items-center space-x-2 ${
                activeTab === 'makeup'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-purple-50'
              }`}
            >
              <Sparkles className="h-5 w-5" />
              <span>Makeup</span>
            </button>
            <button
              onClick={() => setActiveTab('outfit')}
              className={`px-6 py-2 rounded-lg flex items-center space-x-2 ${
                activeTab === 'outfit'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-purple-50'
              }`}
            >
              <Shirt className="h-5 w-5" />
              <span>Outfits</span>
            </button>
            <button
              onClick={() => setActiveTab('products')}
              className={`px-6 py-2 rounded-lg flex items-center space-x-2 ${
                activeTab === 'products'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-purple-50'
              }`}
            >
              <Crown className="h-5 w-5" />
              <span>Products</span>
            </button>
            <button
              onClick={() => setActiveTab('colors')}
              className={`px-6 py-2 rounded-lg flex items-center space-x-2 ${
                activeTab === 'colors'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-purple-50'
              }`}
            >
              <Palette className="h-5 w-5" />
              <span>Color Palettes</span>
            </button>
          </div>
        </div>

        {/* Display error message if any */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {displayError()}
        </div>

        {/* Products Grid */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
          {loading ? (
            <div className="col-span-full text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-purple-600 border-t-transparent" />
            </div>
          ) : (
            <>
              {activeTab === 'makeup' ? (
                // Coming Soon banner for makeup
                <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl p-8 text-white text-center shadow-xl">
                  <div className="max-w-2xl mx-auto">
                    <Sparkles className="h-16 w-16 mx-auto mb-4 opacity-90" />
                    <h2 className="text-3xl font-bold mb-4">Beauty Recommendations</h2>
                    <div className="bg-white bg-opacity-20 rounded-lg px-6 py-3 inline-block mb-4">
                      <span className="text-xl font-semibold">Coming Soon!</span>
                    </div>
                    <p className="text-lg mb-6">
                      We're working on bringing you personalized makeup recommendations based on your unique skin tone. 
                      Our beauty experts are curating the perfect products just for you!
                    </p>
                    <div className="flex justify-center items-center space-x-2 text-sm opacity-90">
                      <Crown className="h-4 w-4" />
                      <span>Premium makeup recommendations launching soon</span>
                    </div>
                  </div>
                </div>
              ) : activeTab === 'products' ? (
                // Coming Soon banner for products
                <div className="bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl p-8 text-white text-center shadow-xl">
                  <div className="max-w-2xl mx-auto">
                    <Crown className="h-16 w-16 mx-auto mb-4 opacity-90" />
                    <h2 className="text-3xl font-bold mb-4">Premium Products</h2>
                    <div className="bg-white bg-opacity-20 rounded-lg px-6 py-3 inline-block mb-4">
                      <span className="text-xl font-semibold">Coming Soon!</span>
                    </div>
                    <p className="text-lg mb-6">
                      We're curating exclusive premium products tailored to your skin tone analysis. 
                      Get ready for personalized product recommendations from top brands!
                    </p>
                    <div className="flex justify-center items-center space-x-2 text-sm opacity-90">
                      <Sparkles className="h-4 w-4" />
                      <span>Premium product collection launching soon</span>
                    </div>
                  </div>
                </div>
              ) : activeTab === 'outfit' ? (
                // Coming Soon banner for outfits
                <div className="bg-gradient-to-r from-green-500 to-teal-500 rounded-xl p-8 text-white text-center shadow-xl">
                  <div className="max-w-2xl mx-auto">
                    <Shirt className="h-16 w-16 mx-auto mb-4 opacity-90" />
                    <h2 className="text-3xl font-bold mb-4">Outfit Recommendations</h2>
                    <div className="bg-white bg-opacity-20 rounded-lg px-6 py-3 inline-block mb-4">
                      <span className="text-xl font-semibold">Coming Soon!</span>
                    </div>
                    <p className="text-lg mb-6">
                      We're curating personalized outfit recommendations that perfectly match your skin tone analysis. 
                      Get ready for style suggestions that will make you look and feel amazing!
                    </p>
                    <div className="flex justify-center items-center space-x-2 text-sm opacity-90">
                      <Sparkles className="h-4 w-4" />
                      <span>Personalized outfit styling launching soon</span>
                    </div>
                  </div>
                </div>
              ) : (
                // Color Palettes Tab - Simplified to only show colors that suit
                <div className="space-y-8">
                  <div className="bg-white rounded-xl p-6 shadow-lg">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Color Recommendations</h2>
                    <p className="text-gray-600 mb-6">
                      Based on your skin tone, we've identified personalized color recommendations that will complement your natural complexion.
                    </p>
                    
                    <div className="flex flex-col md:flex-row md:items-center mb-6 gap-4">
                      <div 
                        className="w-16 h-16 rounded-full shadow-md"
                        style={{ backgroundColor: skinHex }}
                      />
                      <div>
                        <h3 className="text-lg font-semibold">Your Skin Tone</h3>
                        <p className="text-gray-500">{skinHex}</p>
                        {colorRecommendations?.seasonal_type && (
                          <p className="text-purple-600 font-medium">{colorRecommendations.seasonal_type} Color Type</p>
                        )}
                        {monkSkinTone && monkSkinTones[monkSkinTone] && (
                          <div className="text-gray-600 text-sm">
                            <p className="font-medium">{monkSkinTones[monkSkinTone].userFriendlyName}</p>
                            <p className="text-xs text-gray-500">{monkSkinTones[monkSkinTone].seasonalType}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Colors That Suit You */}
                  {colorRecommendations && (
                    <div className="bg-white rounded-xl p-6 shadow-lg">
                      <div className="flex items-center mb-6">
                        <Crown className="w-6 h-6 text-purple-600 mr-2" />
                        <h2 className="text-xl font-bold text-gray-900">Your Color Palette</h2>
                      </div>

                      <div className="space-y-8">
                        {/* Colors That Flatter You */}
                        <div>
                          <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center">
                            <Star className="w-5 h-5 text-yellow-500 mr-2" />
                            Colors That Suit You
                          </h3>
                          
                          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                            {colorRecommendations.colors_that_suit.map((color, index) => (
                              <div key={`${color.hex}-${color.name}-${index}`} className="bg-gray-50 p-3 rounded-lg hover:shadow-md transition-shadow">
                                <div 
                                  className="w-full h-16 rounded-lg shadow-md mb-2"
                                  style={{ backgroundColor: color.hex }}
                                />
                                <span className="text-gray-700 text-sm font-medium block truncate" title={color.name}>
                                  {color.name}
                                </span>
                                <span className="text-gray-500 text-xs">{color.hex}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                        
                        {/* Message about future updates */}
                        {colorRecommendations.message && (
                          <div className="mt-6 p-4 bg-purple-50 rounded-lg">
                            <p className="text-purple-700 italic">{colorRecommendations.message}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default DemoRecommendations;