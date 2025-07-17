import subprocess
import sys
import os

def install_requirements():
    """Install required packages for enhanced skin tone analysis."""
    print("🚀 Setting up Enhanced Skin Tone Analysis")
    print("=" * 50)
    
    requirements = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0", 
        "gradio==4.7.1",
        "tensorflow==2.15.0",
        "scikit-learn==1.3.2",
        "numpy==1.24.3",
        "opencv-python==4.8.1.78",
        "webcolors==1.13",
        "scipy==1.11.4",
        "mediapipe==0.10.7",
        "Pillow==10.1.0",
        "python-multipart==0.0.6",
        "requests==2.31.0"
    ]
    
    print("\n📦 Installing required packages...")
    
    for requirement in requirements:
        try:
            print(f"Installing {requirement}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", requirement])
            print(f"✅ {requirement} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {requirement}: {e}")
            return False
    
    print("\n🎉 All packages installed successfully!")
    return True

def verify_installation():
    """Verify that all packages are installed correctly."""
    print("\n🔍 Verifying installation...")
    
    packages_to_check = [
        "fastapi",
        "uvicorn", 
        "gradio",
        "tensorflow",
        "sklearn",
        "numpy",
        "cv2",
        "webcolors",
        "scipy",
        "mediapipe",
        "PIL",
        "requests"
    ]
    
    all_good = True
    
    for package in packages_to_check:
        try:
            if package == "sklearn":
                __import__("sklearn")
            elif package == "cv2":
                __import__("cv2")
            elif package == "PIL":
                __import__("PIL")
            else:
                __import__(package)
            print(f"✅ {package} is working")
        except ImportError as e:
            print(f"❌ {package} import failed: {e}")
            all_good = False
    
    return all_good

def check_model_file():
    """Check if the model.h5 file exists."""
    print("\n🔍 Checking for model file...")
    
    model_path = "model.h5"
    if os.path.exists(model_path):
        print(f"✅ Model file found: {model_path}")
        return True
    else:
        print(f"⚠️  Model file not found: {model_path}")
        print("   Please make sure your trained model.h5 file is in the backend directory")
        return False

def main():
    """Main setup function."""
    print("🎨 Enhanced Skin Tone Analysis Setup")
    print("This script will install all required dependencies")
    print()
    
    # Install requirements
    if not install_requirements():
        print("❌ Setup failed during package installation")
        return False
    
    # Verify installation
    if not verify_installation():
        print("❌ Setup failed during verification")
        return False
    
    # Check model file
    model_exists = check_model_file()
    
    print("\n" + "=" * 50)
    print("🏁 Setup Summary:")
    print("✅ All Python packages installed")
    print("✅ All imports working correctly")
    print(f"{'✅' if model_exists else '⚠️ '} Model file {'found' if model_exists else 'missing'}")
    
    print("\n📋 Next Steps:")
    print("1. Make sure your model.h5 file is in the backend directory")
    print("2. Run the enhanced API: python enhanced_skin_api.py")
    print("3. Run the enhanced Gradio interface: python enhanced_skin_analysis.py")
    print("4. Test the system: python test_enhanced.py")
    
    print("\n🎯 New Features Available:")
    print("• 👥 Multi-face detection using MediaPipe")
    print("• 💡 Automatic lighting correction (CLAHE)")
    print("• 📊 Confidence scoring with detailed metrics")
    print("• 🎯 Improved color analysis with outlier removal")
    print("• 🚀 Enhanced API with detailed responses")
    
    return True

if __name__ == "__main__":
    main()
