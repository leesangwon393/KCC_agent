import Cocoa

final class HelperApp: NSObject, NSApplicationDelegate {
    var window: NSWindow!
    var message: NSTextField!
    var installing = false
    var ticket: String?
    var process: Process?
    let origin = Bundle.main.object(forInfoDictionaryKey: "MoaOrigin") as? String ?? "https://3.38.192.19"

    func applicationDidFinishLaunching(_ notification: Notification) {
        let menu = NSMenu(); let item = NSMenuItem(); let submenu = NSMenu()
        submenu.addItem(withTitle: "모아 연결 종료", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.submenu = submenu; menu.addItem(item); NSApp.mainMenu = menu
        window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 460, height: 190), styleMask: [.titled, .closable], backing: .buffered, defer: false)
        window.title = "모아 Mac 연결"
        let title = NSTextField(labelWithString: "Mac 연결 프로그램을 준비하고 있어요")
        title.font = .boldSystemFont(ofSize: 19); title.frame = NSRect(x: 28, y: 126, width: 410, height: 28)
        message = NSTextField(wrappingLabelWithString: "처음에는 필요한 프로그램을 자동으로 내려받습니다.\n준비가 끝나면 모아 연결 화면이 열려요.")
        message.frame = NSRect(x: 28, y: 62, width: 405, height: 54)
        let spinner = NSProgressIndicator(frame: NSRect(x: 28, y: 23, width: 24, height: 24))
        spinner.style = .spinning; spinner.startAnimation(nil)
        window.contentView?.addSubview(title); window.contentView?.addSubview(message); window.contentView?.addSubview(spinner)
        window.center(); window.makeKeyAndOrderFront(nil); NSApp.activate(ignoringOtherApps: true)
        start()
    }

    func application(_ application: NSApplication, open urls: [URL]) {
        guard let url = urls.first, url.scheme == "moa-helper", url.host == "connect",
              let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
              components.queryItems?.count == 1,
              let value = components.queryItems?.first, value.name == "ticket", let secret = value.value,
              secret.range(of: "^[A-Za-z0-9_-]{32,128}$", options: .regularExpression) != nil else { return }
        ticket = secret
        if window != nil && !installing { start() }
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        window?.makeKeyAndOrderFront(nil)
        if !installing { start() }
        return true
    }

    func start() {
        guard !installing else { return }; installing = true
        guard let resources = Bundle.main.resourceURL,
              let hash = Bundle.main.object(forInfoDictionaryKey: "MoaSourceSHA256") as? String else { return }
        let data = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/Moa")
        do {
            try FileManager.default.createDirectory(at: data, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
            let logURL = data.appendingPathComponent("installer.log")
            if !FileManager.default.fileExists(atPath: logURL.path) { FileManager.default.createFile(atPath: logURL.path, contents: nil, attributes: [.posixPermissions: 0o600]) }
            let log = try FileHandle(forWritingTo: logURL); log.seekToEndOfFile()
            let job = Process(); process = job; job.executableURL = URL(fileURLWithPath: "/bin/zsh")
            job.arguments = [resources.appendingPathComponent("install-helper.sh").path, resources.appendingPathComponent("source.tar.gz").path, hash, Bundle.main.bundleURL.path, origin]
            job.standardOutput = log; job.standardError = log
            job.terminationHandler = { child in
                try? log.close()
                DispatchQueue.main.async {
                    self.installing = false
                    if child.terminationStatus == 0 { self.finish() }
                    else {
                        self.message.stringValue = "설치를 완료하지 못했어요. 인터넷 연결을 확인하고 다시 열어 주세요."
                        let alert = NSAlert(); alert.messageText = "Mac 연결 준비 실패"; alert.informativeText = "설치 로그에서 원인을 확인할 수 있습니다."
                        alert.addButton(withTitle: "닫기"); alert.addButton(withTitle: "설치 로그 열기")
                        if alert.runModal() == .alertSecondButtonReturn { NSWorkspace.shared.open(logURL) }
                    }
                }
            }
            try job.run()
        } catch { installing = false; message.stringValue = "연결 프로그램을 실행하지 못했어요. 앱을 다시 열어 주세요." }
    }

    func finish() {
        var target = URL(string: origin + "/#onboarding")!
        if let secret = ticket {
            let body: [String: String] = ["origin": origin, "pairing_secret": secret]
            if let json = try? JSONSerialization.data(withJSONObject: body), let fragment = String(data: json, encoding: .utf8) {
                var components = URLComponents(string: "http://127.0.0.1:8000/")!
                components.fragment = "cloud-pair=" + fragment
                if let url = components.url { target = url }
            }
        }
        ticket = nil
        if target.scheme == "http" {
            NSWorkspace.shared.open(target)
        } else {
            let alert = NSAlert(); alert.messageText = "Mac 연결 준비가 끝났어요"
            alert.informativeText = "Dock의 모아 AWS로 돌아가 ‘설치한 앱으로 Mac 연결하기’를 눌러 주세요. 다음부터는 버튼으로 연결 앱이 바로 열립니다."
            alert.addButton(withTitle: "확인"); alert.runModal()
        }
        NSApp.terminate(nil)
    }
}
let app = NSApplication.shared
let delegate = HelperApp(); app.delegate = delegate; app.setActivationPolicy(.regular); app.run()
