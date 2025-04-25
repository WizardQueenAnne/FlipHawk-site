// Continue with other components...
  
  const OpportunityCard = ({ opportunity }) => {
    const { ArrowUpRight, ArrowDownRight, Save, Share2 } = icons;
    
    const profitColor = opportunity.profitPercentage >= 50 ? 'text-green-600' : 
                       opportunity.profitPercentage >= 30 ? 'text-yellow-600' : 
                       'text-red-600';
    
    return (
      <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200">
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-semibold line-clamp-2">{opportunity.title}</h3>
            <span 
              className="px-3 py-1 rounded-full text-sm font-medium text-white"
              style={{ backgroundColor: getConfidenceColor(opportunity.confidence) }}
            >
              {opportunity.confidence}% Match
            </span>
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-sm text-gray-500">Buy Price</p>
              <p className="text-lg font-semibold text-gray-900">${opportunity.buyPrice.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Sell Price</p>
              <p className="text-lg font-semibold text-gray-900">${opportunity.sellPrice.toFixed(2)}</p>
            </div>
          </div>
          
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-gray-500">Net Profit</p>
              <p className={`text-xl font-bold ${profitColor}`}>
                ${opportunity.netProfit.toFixed(2)} ({opportunity.netProfitPercentage.toFixed(1)}%)
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {opportunity.profitPercentage > 0 ? (
                <ArrowUpRight className="w-5 h-5 text-green-500" />
              ) : (
                <ArrowDownRight className="w-5 h-5 text-red-500" />
              )}
            </div>
          </div>
          
          <div className="flex space-x-3">
            <a 
              href={opportunity.buyLink}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md text-center hover:bg-green-700 transition-colors"
            >
              View Buy Listing
            </a>
            <a 
              href={opportunity.sellLink}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md text-center hover:bg-blue-700 transition-colors"
            >
              View Sell Listing
            </a>
          </div>
          
          <div className="mt-4 flex justify-between items-center">
            <div className="flex space-x-2">
              <button 
                onClick={() => saveOpportunity(opportunity)}
                className="p-2 text-gray-600 hover:text-green-600 hover:bg-gray-100 rounded-full"
              >
                <Save className="w-5 h-5" />
              </button>
              <button 
                className="p-2 text-gray-600 hover:text-blue-600 hover:bg-gray-100 rounded-full"
              >
                <Share2 className="w-5 h-5" />
              </button>
            </div>
            <span className="text-sm text-gray-500">
              {opportunity.subcategory}
            </span>
          </div>
        </div>
      </div>
    );
  };

  const ScannerView = () => {
    const { Search } = icons;
    
    return (
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">Find Arbitrage Opportunities</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => {
                  setSelectedCategory(e.target.value);
                  setSelectedSubcategories([]);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-green-500"
              >
                <option value="">Select a category</option>
                {Object.keys(categories).map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </div>
            
            {selectedCategory && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subcategories (select up to 5)
                </label>
                <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto p-2 border border-gray-200 rounded-md">
                  {categories[selectedCategory].map(subcategory => (
                    <label key={subcategory} className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded">
                      <input
                        type="checkbox"
                        checked={selectedSubcategories.includes(subcategory)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            if (selectedSubcategories.length < 5) {
                              setSelectedSubcategories([...selectedSubcategories, subcategory]);
                            }
                          } else {
                            setSelectedSubcategories(selectedSubcategories.filter(item => item !== subcategory));
                          }
                        }}
                        disabled={selectedSubcategories.length >= 5 && !selectedSubcategories.includes(subcategory)}
                        className="rounded border-gray-300 text-green-600 focus:ring-green-500"
                      />
                      <span className="text-sm">{subcategory}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          <button
            onClick={runScan}
            disabled={isLoading || !selectedCategory || selectedSubcategories.length === 0}
            className={`mt-6 w-full py-3 px-4 rounded-md text-white font-medium flex items-center justify-center ${
              isLoading || !selectedCategory || selectedSubcategories.length === 0
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                Scanning...
              </>
            ) : (
              <>
                <Search className="w-5 h-5 mr-2" />
                Find Opportunities
              </>
            )}
          </button>
        </div>
        
        {scanResults.length > 0 && (
          <div className="mb-6">
            <div className="bg-white rounded-lg shadow-md p-4 mb-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <h3 className="text-lg font-semibold">Filter Results</h3>
                <div className="flex flex-wrap gap-4">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600">Min Profit:</label>
                    <input
                      type="number"
                      value={filters.minProfit}
                      onChange={(e) => setFilters(prev => ({ ...prev, minProfit: Number(e.target.value) }))}
                      className="w-24 px-2 py-1 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600">Min Confidence:</label>
                    <select
                      value={filters.minConfidence}
                      onChange={(e) => setFilters(prev => ({ ...prev, minConfidence: Number(e.target.value) }))}
                      className="px-2 py-1 border border-gray-300 rounded-md"
                    >
                      <option value="0">All</option>
                      <option value="70">70%+</option>
                      <option value="80">80%+</option>
                      <option value="90">90%+</option>
                    </select>
                  </div>
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600">Sort by:</label>
                    <select
                      value={filters.sortBy}
                      onChange={(e) => setFilters(prev => ({ ...prev, sortBy: e.target.value }))}
                      className="px-2 py-1 border border-gray-300 rounded-md"
                    >
                      <option value="profitPercentage">Profit %</option>
                      <option value="profit">Profit $</option>
                      <option value="confidence">Confidence</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredResults.map((opportunity, index) => (
                <OpportunityCard key={index} opportunity={opportunity} />
              ))}
            </div>
            
            {filteredResults.length === 0 && (
              <div className="text-center py-8 bg-white rounded-lg shadow-md">
                <p className="text-gray-500">No opportunities match your filters</p>
              </div>
            )}
          </div>
        )}
        
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}
      </div>
    );
  };

  const DashboardView = () => {
    const { Search, CheckCircle, Clock } = icons;
    
    return (
      <div className="max-w-6xl mx-auto">
        <h2 className="text-2xl font-bold mb-6">Performance Dashboard</h2>
        
        {stats ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Total Scans</h3>
                <Search className="w-6 h-6 text-green-500" />
              </div>
              <p className="text-3xl font-bold">{stats.total_scans}</p>
              <p className="text-sm text-gray-500 mt-2">All time</p>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Success Rate</h3>
                <CheckCircle className="w-6 h-6 text-green-500" />
              </div>
              <p className="text-3xl font-bold">{stats.success_rate}%</p>
              <p className="text-sm text-gray-500 mt-2">Successful scans</p>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Avg Scan Time</h3>
                <Clock className="w-6 h-6 text-green-500" />
              </div>
              <p className="text-3xl font-bold">{stats.avg_scan_duration.toFixed(2)}s</p>
              <p className="text-sm text-gray-500 mt-2">Per scan</p>
            </div>
          </div>
        ) : (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
          </div>
        )}
        
        {stats && stats.top_categories && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h3 className="text-lg font-semibold mb-4">Top Categories</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.top_categories}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#22c55e" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <NotificationPanel />
      
      <main className="container mx-auto px-4 py-8">
        {view === 'scan' && <ScannerView />}
        {view === 'dashboard' && <DashboardView />}
        {view === 'saved' && (
          <div className="max-w-6xl mx-auto">
            <h2 className="text-2xl font-bold mb-6">Saved Opportunities</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {savedOpportunities.map((saved, index) => (
                <OpportunityCard key={index} opportunity={saved.opportunity} />
              ))}
            </div>
            {savedOpportunities.length === 0 && (
              <div className="text-center py-8 bg-white rounded-lg shadow-md">
                <p className="text-gray-500">No saved opportunities yet</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};

// Render the application
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  React.createElement(React.StrictMode, null,
    React.createElement(FlipHawkUI)
  )
);

// Service Worker Registration
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('Service Worker registered:', registration);
      })
      .catch(error => {
        console.log('Service Worker registration failed:', error);
      });
  });
}

// Performance monitoring
if (window.performance) {
  window.addEventListener('load', () => {
    setTimeout(() => {
      const timing = window.performance.timing;
      const loadTime = timing.loadEventEnd - timing.navigationStart;
      console.log(`Page load time: ${loadTime}ms`);
      
      // Send metrics to analytics
      if (window.gtag) {
        gtag('event', 'timing_complete', {
          'name': 'load',
          'value': loadTime,
          'event_category': 'Performance'
        });
      }
    }, 0);
  });
}
// FlipHawk Enhanced React Application
const { useState, useEffect, useCallback } = React;
const { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } = Recharts;

// Icon components from Lucide React
const icons = {
  AlertCircle: lucide.AlertCircle,
  TrendingUp: lucide.TrendingUp,
  DollarSign: lucide.DollarSign,
  Package: lucide.Package,
  Clock: lucide.Clock,
  CheckCircle: lucide.CheckCircle,
  XCircle: lucide.XCircle,
  Search: lucide.Search,
  Filter: lucide.Filter,
  ArrowUpRight: lucide.ArrowUpRight,
  ArrowDownRight: lucide.ArrowDownRight,
  Save: lucide.Save,
  Share2: lucide.Share2,
  Bell: lucide.Bell,
  Settings: lucide.Settings,
  LogOut: lucide.LogOut,
  Menu: lucide.Menu,
  X: lucide.X,
  ChevronDown: lucide.ChevronDown,
  ChevronUp: lucide.ChevronUp
};

const FlipHawkUI = () => {
  // State management
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSubcategories, setSelectedSubcategories] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [scanResults, setScanResults] = useState([]);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    minProfit: 0,
    minConfidence: 0,
    sortBy: 'profitPercentage'
  });
  const [stats, setStats] = useState(null);
  const [savedOpportunities, setSavedOpportunities] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [view, setView] = useState('scan');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  
  // Categories and subcategories data
  const categories = {
    "Tech": [
      "Headphones", "Keyboards", "Graphics Cards", "CPUs", "Laptops",
      "Monitors", "SSDs", "Routers", "Vintage Tech"
    ],
    "Collectibles": [
      "Pokémon", "Magic: The Gathering", "Yu-Gi-Oh", "Funko Pops", "Sports Cards",
      "Comic Books", "Action Figures", "LEGO Sets"
    ],
    "Vintage Clothing": [
      "Jordans", "Nike Dunks", "Vintage Tees", "Band Tees", "Denim Jackets",
      "Designer Brands", "Carhartt", "Patagonia"
    ],
    "Antiques": [
      "Coins", "Watches", "Cameras", "Typewriters", "Vinyl Records",
      "Vintage Tools", "Old Maps", "Antique Toys"
    ],
    "Gaming": [
      "Consoles", "Game Controllers", "Rare Games", "Arcade Machines",
      "Handhelds", "Gaming Headsets", "VR Gear"
    ],
    "Music Gear": [
      "Electric Guitars", "Guitar Pedals", "Synthesizers", "Vintage Amps",
      "Microphones", "DJ Equipment"
    ],
    "Tools & DIY": [
      "Power Tools", "Hand Tools", "Welding Equipment", "Toolboxes",
      "Measuring Devices", "Woodworking Tools"
    ],
    "Outdoors & Sports": [
      "Bikes", "Skateboards", "Scooters", "Camping Gear", "Hiking Gear",
      "Fishing Gear", "Snowboards"
    ]
  };

  // Fetch stats on component mount
  useEffect(() => {
    fetchStats();
    loadSavedOpportunities();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const loadSavedOpportunities = async () => {
    try {
      const response = await fetch('/api/v1/my_opportunities');
      const data = await response.json();
      setSavedOpportunities(data);
    } catch (error) {
      console.error('Error loading saved opportunities:', error);
    }
  };

  const runScan = async () => {
    if (!selectedCategory || selectedSubcategories.length === 0) {
      setError('Please select a category and at least one subcategory');
      return;
    }

    setIsLoading(true);
    setError(null);
    setScanResults([]);

    try {
      const response = await fetch('/api/v1/scan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          category: selectedCategory,
          subcategories: selectedSubcategories
        })
      });

      if (!response.ok) {
        throw new Error('Scan failed');
      }

      const data = await response.json();
      setScanResults(data);
      
      // Add notification for completed scan
      addNotification('Scan completed successfully', 'success');
      
    } catch (error) {
      setError('Failed to run scan. Please try again.');
      addNotification('Scan failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const saveOpportunity = async (opportunity) => {
    try {
      const response = await fetch('/api/v1/save_opportunity', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ opportunity })
      });

      if (response.ok) {
        addNotification('Opportunity saved successfully', 'success');
        loadSavedOpportunities();
      }
    } catch (error) {
      addNotification('Failed to save opportunity', 'error');
    }
  };

  const addNotification = (message, type) => {
    const id = Date.now();
    setNotifications(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(notif => notif.id !== id));
    }, 5000);
  };

  const filteredResults = scanResults
    .filter(result => result.profit >= filters.minProfit)
    .filter(result => result.confidence >= filters.minConfidence)
    .sort((a, b) => {
      if (filters.sortBy === 'profitPercentage') {
        return b.profitPercentage - a.profitPercentage;
      } else if (filters.sortBy === 'profit') {
        return b.profit - a.profit;
      } else if (filters.sortBy === 'confidence') {
        return b.confidence - a.confidence;
      }
      return 0;
    });

  const getConfidenceColor = (confidence) => {
    if (confidence >= 90) return '#22c55e';
    if (confidence >= 80) return '#84cc16';
    if (confidence >= 70) return '#eab308';
    return '#ef4444';
  };

  // Components
  const NavBar = () => {
    const { Bell, Settings, Menu, X } = icons;
    
    return (
      <nav className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <div className="flex items-center">
              <img src="/static/logo.png" alt="FlipHawk" className="h-10 w-auto" />
            </div>
            
            <div className="hidden md:flex items-center space-x-6">
              <button 
                onClick={() => setView('scan')}
                className={`px-3 py-2 rounded-md ${view === 'scan' ? 'bg-green-50 text-green-700' : 'text-gray-600 hover:bg-gray-50'}`}
              >
                Scanner
              </button>
              <button 
                onClick={() => setView('dashboard')}
                className={`px-3 py-2 rounded-md ${view === 'dashboard' ? 'bg-green-50 text-green-700' : 'text-gray-600 hover:bg-gray-50'}`}
              >
                Dashboard
              </button>
              <button 
                onClick={() => setView('saved')}
                className={`px-3 py-2 rounded-md ${view === 'saved' ? 'bg-green-50 text-green-700' : 'text-gray-600 hover:bg-gray-50'}`}
              >
                Saved
              </button>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-full"
            >
              <Bell className="w-5 h-5" />
              {notifications.length > 0 && (
                <span className="absolute top-0 right-0 h-4 w-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
                  {notifications.length}
                </span>
              )}
            </button>
            
            <button 
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-gray-600 hover:bg-gray-100 rounded-full"
            >
              <Settings className="w-5 h-5" />
            </button>
            
            <button className="md:hidden p-2 text-gray-600 hover:bg-gray-100 rounded-full" onClick={() => setShowMobileMenu(!showMobileMenu)}>
              {showMobileMenu ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
        
        {/* Mobile menu */}
        {showMobileMenu && (
          <div className="md:hidden mt-3 border-t border-gray-200 pt-3">
            <button 
              onClick={() => { setView('scan'); setShowMobileMenu(false); }}
              className={`block w-full text-left px-3 py-2 rounded-md ${view === 'scan' ? 'bg-green-50 text-green-700' : 'text-gray-600'}`}
            >
              Scanner
            </button>
            <button 
              onClick={() => { setView('dashboard'); setShowMobileMenu(false); }}
              className={`block w-full text-left px-3 py-2 rounded-md ${view === 'dashboard' ? 'bg-green-50 text-green-700' : 'text-gray-600'}`}
            >
              Dashboard
            </button>
            <button 
              onClick={() => { setView('saved'); setShowMobileMenu(false); }}
              className={`block w-full text-left px-3 py-2 rounded-md ${view === 'saved' ? 'bg-green-50 text-green-700' : 'text-gray-600'}`}
            >
              Saved
            </button>
          </div>
        )}
      </nav>
    );
  };

  const NotificationPanel = () => {
    const { CheckCircle, XCircle, AlertCircle } = icons;
    
    return showNotifications && (
      <div className="absolute right-4 top-16 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
        <div className="p-4 border-b border-gray-200">
          <h3 className="font-semibold">Notifications</h3>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="p-4 text-center text-gray-500">No notifications</div>
          ) : (
            notifications.map(notif => (
              <div 
                key={notif.id} 
                className={`p-4 border-b border-gray-100 flex items-start ${
                  notif.type === 'success' ? 'bg-green-50' : 
                  notif.type === 'error' ? 'bg-red-50' : 
                  'bg-blue-50'
                }`}
              >
                {notif.type === 'success' ? (
                  <CheckCircle className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                ) : notif.type === 'error' ? (
                  <XCircle className="w-5 h-5 text-red-500 mr-3 flex-shrink-0" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-blue-500 mr-3 flex-shrink-0" />
                )}
                <span className="text-sm">{notif.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  // Continue with other components...
  
  // (I'll continue in the next response due to length limits)
