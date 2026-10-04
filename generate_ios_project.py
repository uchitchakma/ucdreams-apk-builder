import os
import sys
import argparse
import base64
import shutil
import json
import io
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--app-name', default='My App')
parser.add_argument('--bundle-id', default='com.myapp.app')
parser.add_argument('--web-url', default='https://example.com')
parser.add_argument('--theme-color', default='#0284c7')
parser.add_argument('--build-id', default='ucd_1')
parser.add_argument('--icon-base64', default='')
args = parser.parse_args()

app_name = args.app_name.strip() or 'My App'
bundle_id = args.bundle_id.strip() or 'com.myapp.app'
web_url = args.web_url.strip() or 'https://example.com'
theme_color = args.theme_color.strip() or '#0284c7'
build_id = args.build_id.strip() or 'ucd_1'
icon_base64 = args.icon_base64.strip()

out_dir = os.path.abspath('ios_project')
if os.path.exists(out_dir):
    shutil.rmtree(out_dir)
os.makedirs(out_dir, exist_ok=True)

app_dir = os.path.join(out_dir, 'App')
proj_dir = os.path.join(out_dir, 'App.xcodeproj')
assets_dir = os.path.join(app_dir, 'Assets.xcassets')
icon_dir = os.path.join(assets_dir, 'AppIcon.appiconset')
base_lproj = os.path.join(app_dir, 'Base.lproj')

for d in [app_dir, proj_dir, assets_dir, icon_dir, base_lproj]:
    os.makedirs(d, exist_ok=True)

# 1. Generate Icons
temp_icon = os.path.join(out_dir, 'temp_icon_1024.png')
has_icon = False
if icon_base64:
    try:
        if ',' in icon_base64:
            icon_base64 = icon_base64.split(',', 1)[1]
        raw_data = base64.b64decode(icon_base64)
        with open(temp_icon, 'wb') as f:
            f.write(raw_data)
        has_icon = True
    except Exception as e:
        print('Icon decode error:', e)

icon_sizes = [
    (20, '20x20', '1x'),
    (40, '20x20', '2x'),
    (60, '20x20', '3x'),
    (29, '29x29', '1x'),
    (58, '29x29', '2x'),
    (87, '29x29', '3x'),
    (40, '40x40', '1x'),
    (80, '40x40', '2x'),
    (120, '40x40', '3x'),
    (120, '60x60', '2x'),
    (180, '60x60', '3x'),
    (1024, '1024x1024', '1x')
]

contents_json = {'images': [], 'info': {'author': 'xcode', 'version': 1}}

# Try Pillow first, then macOS sips
use_pillow = False
try:
    from PIL import Image
    use_pillow = True
    if has_icon:
        base_img = Image.open(temp_icon).convert('RGBA')
    else:
        base_img = Image.new('RGBA', (1024, 1024), theme_color)
    
    for px, size_str, scale_str in icon_sizes:
        fname = f'icon_{px}x{px}.png'
        resized = base_img.resize((px, px), Image.Resampling.LANCZOS)
        resized.save(os.path.join(icon_dir, fname), 'PNG')
        contents_json['images'].append({
            'size': size_str,
            'idiom': 'universal' if px == 1024 else 'iphone',
            'filename': fname,
            'scale': scale_str
        })
except Exception:
    use_pillow = False

if not use_pillow:
    # If no base icon, create a basic 1024x1024 using sips or python
    if not has_icon:
        # Create minimal 1024x1024 PNG with python
        import struct, zlib
        width = 1024
        height = 1024
        r = int(theme_color.lstrip('#')[0:2], 16) if len(theme_color.lstrip('#')) >= 6 else 2
        g = int(theme_color.lstrip('#')[2:4], 16) if len(theme_color.lstrip('#')) >= 6 else 132
        b = int(theme_color.lstrip('#')[4:6], 16) if len(theme_color.lstrip('#')) >= 6 else 199
        row = b'\x00' + bytes([r, g, b, 255]) * width
        raw = row * height
        compressed = zlib.compress(raw)
        
        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        
        png_bytes = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', compressed) + chunk(b'IEND', b'')
        with open(temp_icon, 'wb') as f:
            f.write(png_bytes)
    
    for px, size_str, scale_str in icon_sizes:
        fname = f'icon_{px}x{px}.png'
        target_path = os.path.join(icon_dir, fname)
        subprocess.run(['sips', '-z', str(px), str(px), temp_icon, '--out', target_path], capture_output=True)
        contents_json['images'].append({
            'size': size_str,
            'idiom': 'universal' if px == 1024 else 'iphone',
            'filename': fname,
            'scale': scale_str
        })

with open(os.path.join(icon_dir, 'Contents.json'), 'w') as f:
    json.dump(contents_json, f, indent=2)

with open(os.path.join(assets_dir, 'Contents.json'), 'w') as f:
    json.dump({'info': {'author': 'xcode', 'version': 1}}, f, indent=2)

# Clean up temp
if os.path.exists(temp_icon):
    os.remove(temp_icon)

# 2. AppDelegate.swift
app_delegate = """import UIKit

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?

    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        return true
    }

    func application(_ application: UIApplication, configurationForConnecting connectingSceneSession: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        return UISceneConfiguration(name: "Default Configuration", sessionRole: connectingSceneSession.role)
    }
}
"""
with open(os.path.join(app_dir, 'AppDelegate.swift'), 'w') as f:
    f.write(app_delegate)

# 3. SceneDelegate.swift
scene_delegate = """import UIKit

class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
        guard let _ = (scene as? UIWindowScene) else { return }
    }
}
"""
with open(os.path.join(app_dir, 'SceneDelegate.swift'), 'w') as f:
    f.write(scene_delegate)

# 4. ViewController.swift
view_controller = f"""import UIKit
import WebKit

class ViewController: UIViewController, WKNavigationDelegate, WKUIDelegate {{
    var webView: WKWebView!
    var progressView: UIProgressView!

    override func viewDidLoad() {{
        super.viewDidLoad()
        setupWebView()
        setupProgressBar()
        loadTargetURL()
    }}

    func setupWebView() {{
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []
        
        let prefs = WKWebpagePreferences()
        prefs.allowsContentJavaScript = true
        config.defaultWebpagePreferences = prefs

        webView = WKWebView(frame: view.bounds, configuration: config)
        webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.allowsBackForwardNavigationGestures = true
        webView.scrollView.bounces = true
        webView.scrollView.contentInsetAdjustmentBehavior = .automatic
        
        view.addSubview(webView)
    }}

    func setupProgressBar() {{
        progressView = UIProgressView(progressViewStyle: .default)
        progressView.translatesAutoresizingMaskIntoConstraints = false
        progressView.tintColor = UIColor(hex: "{theme_color}") ?? .systemBlue
        progressView.trackTintColor = .clear
        view.addSubview(progressView)

        NSLayoutConstraint.activate([
            progressView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            progressView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            progressView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            progressView.heightAnchor.constraint(equalToConstant: 2.5)
        ])

        webView.addObserver(self, forKeyPath: #keyPath(WKWebView.estimatedProgress), options: .new, context: nil)
    }}

    func loadTargetURL() {{
        if let url = URL(string: "{web_url}") {{
            var request = URLRequest(url: url)
            request.timeoutInterval = 30
            webView.load(request)
        }}
    }}

    override func observeValue(forKeyPath keyPath: String?, of object: Any?, change: [NSKeyValueChangeKey : Any]?, context: UnsafeMutableRawPointer?) {{
        if keyPath == "estimatedProgress" {{
            progressView.progress = Float(webView.estimatedProgress)
            progressView.isHidden = webView.estimatedProgress >= 1.0
        }}
    }}

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {{
        progressView.isHidden = true
    }}

    deinit {{
        webView.removeObserver(self, forKeyPath: #keyPath(WKWebView.estimatedProgress))
    }}
}}

extension UIColor {{
    convenience init?(hex: String) {{
        var cString = hex.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        if cString.hasPrefix("#") {{ cString.remove(at: cString.startIndex) }}
        guard cString.count == 6 else {{ return nil }}
        var rgbValue: UInt64 = 0
        Scanner(string: cString).scanHexInt64(&rgbValue)
        self.init(
            red: CGFloat((rgbValue & 0xFF0000) >> 16) / 255.0,
            green: CGFloat((rgbValue & 0x00FF00) >> 8) / 255.0,
            blue: CGFloat(rgbValue & 0x0000FF) / 255.0,
            alpha: 1.0
        )
    }}
}}
"""
with open(os.path.join(app_dir, 'ViewController.swift'), 'w') as f:
    f.write(view_controller)

# 5. Info.plist
info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>$(DEVELOPMENT_LANGUAGE)</string>
    <key>CFBundleDisplayName</key>
    <string>{app_name}</string>
    <key>CFBundleExecutable</key>
    <string>$(EXECUTABLE_NAME)</string>
    <key>CFBundleIdentifier</key>
    <string>{bundle_id}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>$(PRODUCT_NAME)</string>
    <key>CFBundlePackageType</key>
    <string>$(PRODUCT_BUNDLE_PACKAGE_TYPE)</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSRequiresIPhoneOS</key>
    <true/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
    <key>NSCameraUsageDescription</key>
    <string>{app_name} requires camera access to capture photos and scan codes.</string>
    <key>NSLocationWhenInUseUsageDescription</key>
    <string>{app_name} requires location access to provide location-based services.</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>{app_name} requires microphone access for audio recordings.</string>
    <key>NSPhotoLibraryUsageDescription</key>
    <string>{app_name} requires photo library access to upload images.</string>
    <key>UIApplicationSceneManifest</key>
    <dict>
        <key>UIApplicationSupportsMultipleScenes</key>
        <false/>
        <key>UISceneConfigurations</key>
        <dict>
            <key>UIWindowSceneSessionRoleApplication</key>
            <array>
                <dict>
                    <key>UISceneConfigurationName</key>
                    <string>Default Configuration</string>
                    <key>UISceneDelegateClassName</key>
                    <string>$(PRODUCT_MODULE_NAME).SceneDelegate</string>
                    <key>UISceneStoryboardFile</key>
                    <string>Main</string>
                </dict>
            </array>
        </dict>
    </dict>
    <key>UIApplicationSupportsIndirectInputEvents</key>
    <true/>
    <key>UILaunchStoryboardName</key>
    <string>LaunchScreen</string>
    <key>UIMainStoryboardFile</key>
    <string>Main</string>
    <key>UIRequiredDeviceCapabilities</key>
    <array>
        <string>armv7</string>
    </array>
    <key>UISupportedInterfaceOrientations</key>
    <array>
        <string>UIInterfaceOrientationPortrait</string>
        <string>UIInterfaceOrientationLandscapeLeft</string>
        <string>UIInterfaceOrientationLandscapeRight</string>
    </array>
</dict>
</plist>
"""
with open(os.path.join(app_dir, 'Info.plist'), 'w') as f:
    f.write(info_plist)

# 6. Main.storyboard
main_storyboard = """<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0" toolsVersion="21701" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES" initialViewController="BYZ-38-t0r">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="21678"/>
        <capability name="Safe area layout guides" minToolsVersion="9.0"/>
        <capability name="System colors in document resources" minToolsVersion="11.0"/>
        <capability name="documents saved in the Xcode 8 format" minToolsVersion="8.0"/>
    </dependencies>
    <scenes>
        <scene sceneID="tne-QT-ifu">
            <objects>
                <viewController id="BYZ-38-t0r" customClass="ViewController" customModule="App" customModuleProvider="target" sceneMemberID="viewController">
                    <view key="view" contentMode="scaleToFill" id="8bC-Xf-vdC">
                        <rect key="frame" x="0.0" y="0.0" width="393" height="852"/>
                        <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
                        <viewLayoutGuide key="safeArea" id="6Tk-OE-BBY"/>
                        <color key="backgroundColor" systemColor="systemBackgroundColor"/>
                    </view>
                </viewController>
                <placeholder placeholderIdentifier="IBFirstResponder" id="dkx-z0-nzr" sceneMemberID="firstResponder"/>
            </objects>
            <point key="canvasLocation" x="131" y="-28"/>
        </scene>
    </scenes>
    <resources>
        <systemColor name="systemBackgroundColor">
            <color white="1" alpha="1" colorSpace="custom" customColorSpace="genericGamma22GrayColorSpace"/>
        </systemColor>
    </resources>
</document>
"""
with open(os.path.join(base_lproj, 'Main.storyboard'), 'w') as f:
    f.write(main_storyboard)

# 7. LaunchScreen.storyboard
r_val = int(theme_color.lstrip('#')[0:2], 16) / 255.0 if len(theme_color.lstrip('#')) >= 6 else 0.0
g_val = int(theme_color.lstrip('#')[2:4], 16) / 255.0 if len(theme_color.lstrip('#')) >= 6 else 0.5
b_val = int(theme_color.lstrip('#')[4:6], 16) / 255.0 if len(theme_color.lstrip('#')) >= 6 else 0.8

launch_storyboard = f"""<?xml version="1.0" encoding="UTF-8"?>
<document type="com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB" version="3.0" toolsVersion="21701" targetRuntime="iOS.CocoaTouch" propertyAccessControl="none" useAutolayout="YES" launchScreen="YES" useTraitCollections="YES" useSafeAreas="YES" colorMatched="YES" initialViewController="01J-lp-oVM">
    <device id="retina6_12" orientation="portrait" appearance="light"/>
    <dependencies>
        <plugIn identifier="com.apple.InterfaceBuilder.IBCocoaTouchPlugin" version="21678"/>
        <capability name="Safe area layout guides" minToolsVersion="9.0"/>
        <capability name="documents saved in the Xcode 8 format" minToolsVersion="8.0"/>
    </dependencies>
    <scenes>
        <scene sceneID="EHf-IW-A2E">
            <objects>
                <viewController id="01J-lp-oVM" sceneMemberID="viewController">
                    <view key="view" contentMode="scaleToFill" id="Ze5-6b-2t3">
                        <rect key="frame" x="0.0" y="0.0" width="393" height="852"/>
                        <autoresizingMask key="autoresizingMask" widthSizable="YES" heightSizable="YES"/>
                        <subviews>
                            <label opaque="NO" clipsSubviews="YES" userInteractionEnabled="NO" contentMode="left" horizontalHuggingPriority="251" verticalHuggingPriority="251" text="{app_name}" textAlignment="center" lineBreakMode="middleTruncation" baselineAdjustment="alignBaselines" minimumFontSize="18" translatesAutoresizingMaskIntoConstraints="NO" id="GJd-Yh-RWb">
                                <rect key="frame" x="20" y="404.66666666666669" width="353" height="43"/>
                                <fontDescription key="fontDescription" type="boldSystem" pointSize="36"/>
                                <color key="textColor" white="1" alpha="1" colorSpace="custom" customColorSpace="genericGamma22GrayColorSpace"/>
                                <nil key="highlightedColor"/>
                            </label>
                        </subviews>
                        <viewLayoutGuide key="safeArea" id="Bcu-3y-fUS"/>
                        <color key="backgroundColor" red="{r_val:.3f}" green="{g_val:.3f}" blue="{b_val:.3f}" alpha="1" colorSpace="custom" customColorSpace="sRGB"/>
                        <constraints>
                            <constraint firstItem="Bcu-3y-fUS" firstAttribute="centerX" secondItem="GJd-Yh-RWb" secondAttribute="centerX" id="Q3B-4B-g5h"/>
                            <constraint firstItem="GJd-Yh-RWb" firstAttribute="centerY" secondItem="Ze5-6b-2t3" secondAttribute="centerY" id="moa-c2-u7t"/>
                            <constraint firstItem="GJd-Yh-RWb" firstAttribute="leading" secondItem="Bcu-3y-fUS" secondAttribute="leading" constant="20" symbolic="YES" id="x7j-FC-K8j"/>
                        </constraints>
                    </view>
                </viewController>
                <placeholder placeholderIdentifier="IBFirstResponder" id="iYj-Kq-Ea1" userLabel="First Responder" sceneMemberID="firstResponder"/>
            </objects>
            <point key="canvasLocation" x="53" y="375"/>
        </scene>
    </scenes>
</document>
"""
with open(os.path.join(base_lproj, 'LaunchScreen.storyboard'), 'w') as f:
    f.write(launch_storyboard)

# 8. project.pbxproj
pbxproj = f"""// !$*UTF8*$!
{{
	archiveVersion = 1;
	classes = {{
	}};
	objectVersion = 56;
	objects = {{

/* Begin PBXBuildFile section */
		A10000012900000100000001 /* AppDelegate.swift in Sources */ = {{isa = PBXBuildFile; fileRef = B10000012900000100000001 /* AppDelegate.swift */; }};
		A10000022900000100000001 /* SceneDelegate.swift in Sources */ = {{isa = PBXBuildFile; fileRef = B10000022900000100000001 /* SceneDelegate.swift */; }};
		A10000032900000100000001 /* ViewController.swift in Sources */ = {{isa = PBXBuildFile; fileRef = B10000032900000100000001 /* ViewController.swift */; }};
		A10000042900000100000001 /* Main.storyboard in Resources */ = {{isa = PBXBuildFile; fileRef = B10000042900000100000001 /* Main.storyboard */; }};
		A10000052900000100000001 /* Assets.xcassets in Resources */ = {{isa = PBXBuildFile; fileRef = B10000052900000100000001 /* Assets.xcassets */; }};
		A10000062900000100000001 /* LaunchScreen.storyboard in Resources */ = {{isa = PBXBuildFile; fileRef = B10000062900000100000001 /* LaunchScreen.storyboard */; }};
/* End PBXBuildFile section */

/* Begin PBXFileReference section */
		C10000012900000100000001 /* App.app */ = {{isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = App.app; sourceTree = BUILT_PRODUCTS_DIR; }};
		B10000012900000100000001 /* AppDelegate.swift */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = AppDelegate.swift; sourceTree = "<group>"; }};
		B10000022900000100000001 /* SceneDelegate.swift */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = SceneDelegate.swift; sourceTree = "<group>"; }};
		B10000032900000100000001 /* ViewController.swift */ = {{isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = ViewController.swift; sourceTree = "<group>"; }};
		B10000042900000100000001 /* Main.storyboard */ = {{isa = PBXFileReference; lastKnownFileType = file.storyboard; path = Base.lproj/Main.storyboard; sourceTree = "<group>"; }};
		B10000052900000100000001 /* Assets.xcassets */ = {{isa = PBXFileReference; lastKnownFileType = folder.assetcatalog; path = Assets.xcassets; sourceTree = "<group>"; }};
		B10000062900000100000001 /* LaunchScreen.storyboard */ = {{isa = PBXFileReference; lastKnownFileType = file.storyboard; path = Base.lproj/LaunchScreen.storyboard; sourceTree = "<group>"; }};
		B10000072900000100000001 /* Info.plist */ = {{isa = PBXFileReference; lastKnownFileType = text.plist.xml; path = Info.plist; sourceTree = "<group>"; }};
/* End PBXFileReference section */

/* Begin PBXFrameworksBuildPhase section */
		D10000012900000100000001 /* Frameworks */ = {{
			isa = PBXFrameworksBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		}};
/* End PBXFrameworksBuildPhase section */

/* Begin PBXGroup section */
		E10000012900000100000001 = {{
			isa = PBXGroup;
			children = (
				E10000022900000100000001 /* App */,
				E10000032900000100000001 /* Products */,
			);
			sourceTree = "<group>";
		}};
		E10000022900000100000001 /* App */ = {{
			isa = PBXGroup;
			children = (
				B10000012900000100000001 /* AppDelegate.swift */,
				B10000022900000100000001 /* SceneDelegate.swift */,
				B10000032900000100000001 /* ViewController.swift */,
				B10000042900000100000001 /* Main.storyboard */,
				B10000052900000100000001 /* Assets.xcassets */,
				B10000062900000100000001 /* LaunchScreen.storyboard */,
				B10000072900000100000001 /* Info.plist */,
			);
			path = App;
			sourceTree = "<group>";
		}};
		E10000032900000100000001 /* Products */ = {{
			isa = PBXGroup;
			children = (
				C10000012900000100000001 /* App.app */,
			);
			name = Products;
			sourceTree = "<group>";
		}};
/* End PBXGroup section */

/* Begin PBXNativeTarget section */
		F10000012900000100000001 /* App */ = {{
			isa = PBXNativeTarget;
			buildConfigurationList = G10000012900000100000001 /* Build configuration list for PBXNativeTarget "App" */;
			buildPhases = (
				H10000012900000100000001 /* Sources */,
				D10000012900000100000001 /* Frameworks */,
				I10000012900000100000001 /* Resources */,
			);
			buildRules = (
			);
			dependencies = (
			);
			name = App;
			productName = App;
			productReference = C10000012900000100000001 /* App.app */;
			productType = "com.apple.product-type.application";
		}};
/* End PBXNativeTarget section */

/* Begin PBXProject section */
		J10000012900000100000001 /* Project object */ = {{
			isa = PBXProject;
			attributes = {{
				BuildIndependentTargetsInParallel = 1;
				LastSwiftUpdateCheck = 1430;
				LastUpgradeCheck = 1430;
				TargetAttributes = {{
					F10000012900000100000001 = {{
						CreatedOnToolsVersion = 14.3;
					}};
				}};
			}};
			buildConfigurationList = G10000022900000100000001 /* Build configuration list for PBXProject "App" */;
			compatibilityVersion = "Xcode 14.0";
			developmentRegion = en;
			hasScannedForEncodings = 0;
			knownRegions = (
				en,
				Base,
			);
			mainGroup = E10000012900000100000001;
			productRefGroup = E10000032900000100000001 /* Products */;
			projectDirPath = "";
			projectRoot = "";
			targets = (
				F10000012900000100000001 /* App */,
			);
		}};
/* End PBXProject section */

/* Begin PBXResourcesBuildPhase section */
		I10000012900000100000001 /* Resources */ = {{
			isa = PBXResourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
				A10000062900000100000001 /* LaunchScreen.storyboard in Resources */,
				A10000052900000100000001 /* Assets.xcassets in Resources */,
				A10000042900000100000001 /* Main.storyboard in Resources */,
			);
			runOnlyForDeploymentPostprocessing = 0;
		}};
/* End PBXResourcesBuildPhase section */

/* Begin PBXSourcesBuildPhase section */
		H10000012900000100000001 /* Sources */ = {{
			isa = PBXSourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
				A10000032900000100000001 /* ViewController.swift in Sources */,
				A10000012900000100000001 /* AppDelegate.swift in Sources */,
				A10000022900000100000001 /* SceneDelegate.swift in Sources */,
			);
			runOnlyForDeploymentPostprocessing = 0;
		}};
/* End PBXSourcesBuildPhase section */

/* Begin XCBuildConfiguration section */
		K10000012900000100000001 /* Debug */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				ALWAYS_SEARCH_USER_PATHS = NO;
				CLANG_ANALYZER_NONNULL = YES;
				CLANG_CXX_LANGUAGE_STANDARD = "gnu++20";
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = dwarf;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				ENABLE_TESTABILITY = YES;
				GCC_DYNAMIC_NO_PIC = NO;
				GCC_OPTIMIZATION_LEVEL = 0;
				GCC_PREPROCESSOR_DEFINITIONS = (
					"DEBUG=1",
					"$(inherited)",
				);
				GCC_WARN_UNINITIALIZED_AUTOS = YES_AGGRESSIVE;
				IPHONEOS_DEPLOYMENT_TARGET = 14.0;
				MTL_ENABLE_DEBUG_INFO = INCLUDE_SOURCE;
				ONLY_ACTIVE_ARCH = YES;
				SDKROOT = iphoneos;
				SWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG;
				SWIFT_OPTIMIZATION_LEVEL = "-Onone";
			}};
			name = Debug;
		}};
		K10000022900000100000001 /* Release */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				ALWAYS_SEARCH_USER_PATHS = NO;
				CLANG_ANALYZER_NONNULL = YES;
				CLANG_CXX_LANGUAGE_STANDARD = "gnu++20";
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = "dwarf-with-dsym";
				ENABLE_NS_ASSERTIONS = NO;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				GCC_OPTIMIZATION_LEVEL = s;
				GCC_WARN_UNINITIALIZED_AUTOS = YES_AGGRESSIVE;
				IPHONEOS_DEPLOYMENT_TARGET = 14.0;
				MTL_ENABLE_DEBUG_INFO = NO;
				SDKROOT = iphoneos;
				SWIFT_COMPILATION_MODE = wholemodule;
				SWIFT_OPTIMIZATION_LEVEL = "-O";
				VALIDATE_PRODUCT = YES;
			}};
			name = Release;
		}};
		K10000032900000100000001 /* Debug */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
				CODE_SIGN_STYLE = Automatic;
				CURRENT_PROJECT_VERSION = 1;
				GENERATE_INFOPLIST_FILE = NO;
				INFOPLIST_FILE = App/Info.plist;
				INFOPLIST_KEY_CFBundleDisplayName = "{app_name}";
				LD_RUNPATH_SEARCH_PATHS = (
					"$(inherited)",
					"@executable_path/Frameworks",
				);
				MARKETING_VERSION = 1.0.0;
				PRODUCT_BUNDLE_IDENTIFIER = "{bundle_id}";
				PRODUCT_NAME = "$(TARGET_NAME)";
				SWIFT_EMIT_LOC_STRINGS = YES;
				SWIFT_VERSION = 5.0;
				TARGETED_DEVICE_FAMILY = "1,2";
			}};
			name = Debug;
		}};
		K10000042900000100000001 /* Release */ = {{
			isa = XCBuildConfiguration;
			buildSettings = {{
				ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
				CODE_SIGN_STYLE = Automatic;
				CURRENT_PROJECT_VERSION = 1;
				GENERATE_INFOPLIST_FILE = NO;
				INFOPLIST_FILE = App/Info.plist;
				INFOPLIST_KEY_CFBundleDisplayName = "{app_name}";
				LD_RUNPATH_SEARCH_PATHS = (
					"$(inherited)",
					"@executable_path/Frameworks",
				);
				MARKETING_VERSION = 1.0.0;
				PRODUCT_BUNDLE_IDENTIFIER = "{bundle_id}";
				PRODUCT_NAME = "$(TARGET_NAME)";
				SWIFT_EMIT_LOC_STRINGS = YES;
				SWIFT_VERSION = 5.0;
				TARGETED_DEVICE_FAMILY = "1,2";
			}};
			name = Release;
		}};
/* End XCBuildConfiguration section */

/* Begin XCConfigurationList section */
		G10000012900000100000001 /* Build configuration list for PBXNativeTarget "App" */ = {{
			isa = XCConfigurationList;
			buildConfigurations = (
				K10000032900000100000001 /* Debug */,
				K10000042900000100000001 /* Release */,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		}};
		G10000022900000100000001 /* Build configuration list for PBXProject "App" */ = {{
			isa = XCConfigurationList;
			buildConfigurations = (
				K10000012900000100000001 /* Debug */,
				K10000022900000100000001 /* Release */,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		}};
/* End XCConfigurationList section */

	}};
	rootObject = J10000012900000100000001 /* Project object */;
}}
"""
with open(os.path.join(proj_dir, 'project.pbxproj'), 'w') as f:
    f.write(pbxproj)

print(f"Successfully generated iOS project for {app_name} ({bundle_id}) at {out_dir}")
