import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { Star, Sparkles, Crown, Shirt, Palette } from 'lucide-react';
import ProductRecommendations from '../components/ProductRecommendations';
import { API_ENDPOINTS, buildApiUrl } from '../config/api';

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
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [skinAnalysis, setSkinAnalysis] = useState<SkinAnalysisResult | null>(null);
  const [skinHex, setSkinHex] = useState<string>('#d7bd96'); // Default skin hex
  const [monkSkinTone, setMonkSkinTone] = useState<string>('Monk05'); // Default Monk skin tone
  const [activeTab, setActiveTab] = useState<'makeup' | 'outfit' | 'colors'>('makeup');
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

  // Fetch color recommendations
  useEffect(() => {
    const fetchColorRecommendations = async () => {
      if (activeTab === 'colors' && (skinHex || monkSkinTone)) {
        try {
          // Build query parameters
          const queryParams = new URLSearchParams();
          
          // Add hex color if available
          if (skinHex) {
            queryParams.append('hex_color', skinHex.replace('#', ''));
          }
          
          // Add Monk skin tone if available
          if (monkSkinTone) {
            queryParams.append('skin_tone', monkSkinTone);
          }
          
          const response = await fetch(buildApiUrl(API_ENDPOINTS.COLOR_RECOMMENDATIONS, Object.fromEntries(queryParams)));
          if (response.ok) {
            const data = await response.json();
            setColorRecommendations(data);
          } else {
            console.error('Failed to fetch color recommendations');
            setError('Failed to fetch color recommendations. Please try again later.');
          }
        } catch (err) {
          console.error('Error fetching color recommendations:', err);
          setError('Error connecting to the server. Please check your connection and try again.');
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
            throw new Error(`Failed to fetch makeup recommendations: ${response.status} ${response.statusText}`);
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
              console.error('Error fetching makeup types:', err);
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
            throw new Error(`Failed to fetch outfit recommendations: ${response.status} ${response.statusText}`);
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
        setError(err instanceof Error ? err.message : 'An error occurred');
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
        const analysisArray = JSON.parse(storedAnalysis);
        if (analysisArray && analysisArray.length >= 2) {
          setSkinAnalysis(analysisArray[0]);
          setSkinHex(analysisArray[1]);
          
          // Determine Monk skin tone from hex color
          const hexColor = analysisArray[1];
          const monkId = determineMonkSkinTone(hexColor);
          setMonkSkinTone(monkId);
        }
      }
    } catch (err) {
      console.error('Error loading skin analysis from session storage:', err);
      setError('Error loading your skin analysis. Please try analyzing your skin again.');
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

  return (
    <Layout>
      <div className="min-h-screen bg-gray-50">
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
                <ProductRecommendations 
                  skinTone={skinAnalysis?.label || ''}
                  products={products}
                  type={activeTab}
                  totalItems={totalItems}
                  totalPages={totalPages}
                  currentPage={currentPage}
                  onPageChange={handlePageChange}
                  onFilterChange={handleFilterChange}
                  availableFilters={availableFilters}
                />
              ) : activeTab === 'outfit' ? (
                <ProductRecommendations 
                  skinTone={skinAnalysis?.label || ''}
                  products={products}
                  type={activeTab}
                  totalItems={totalItems}
                  totalPages={totalPages}
                  currentPage={currentPage}
                  onPageChange={handlePageChange}
                />
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
                        {colorRecommendations?.monk_skin_tone && (
                          <p className="text-gray-600 text-sm">{colorRecommendations.monk_skin_tone}</p>
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
                            {colorRecommendations.colors_that_suit.map((color) => (
                              <div key={color.hex} className="bg-gray-50 p-3 rounded-lg hover:shadow-md transition-shadow">
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