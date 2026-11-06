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
        guard let secret = ticket else {
            message.stringValue = "준비가 끝났어요. 모아 웹앱에서 ‘설치한 앱으로 Mac 연결하기’를 눌러 주세요."
            return
        }
        ticket = nil
        let alert = NSAlert()
        alert.messageText = "이 Mac을 모아에 연결할까요?"
        alert.informativeText = "연결 주소: \(origin)\n다음 화면에서 모아가 사용할 폴더를 선택합니다. 선택한 폴더의 파일 이름을 QWEN이 Mac에서 살펴보고 정리 지침(_project.md)을 만듭니다. 기존 지침은 보존합니다. 파일 분류 상태는 모아 계정에 표시됩니다."
        alert.addButton(withTitle: "폴더 선택하기")
        alert.addButton(withTitle: "취소")
        guard alert.runModal() == .alertFirstButtonReturn else {
            message.stringValue = "연결을 취소했어요. 모아 웹앱에서 다시 시도할 수 있습니다."
            return
        }
        let picker = NSOpenPanel()
        picker.title = "모아가 접근할 폴더를 모두 선택해 주세요"
        picker.message = "⌘ 키를 누른 채 여러 폴더를 선택할 수 있어요. 선택을 마치면 QWEN이 각 폴더의 정리 지침 README(_project.md)를 작성합니다. 기존 README는 변경하지 않습니다."
        picker.prompt = "선택 완료 · 지침 만들기"
        picker.canChooseFiles = false
        picker.canChooseDirectories = true
        picker.allowsMultipleSelection = true
        picker.canCreateDirectories = false
        guard picker.runModal() == .OK, !picker.urls.isEmpty else {
            message.stringValue = "폴더 선택을 취소했어요. 모아 웹앱에서 다시 연결할 수 있습니다."
            return
        }
        let folders = picker.urls.map { $0.path }
        guard folders.count <= 20 else {
            message.stringValue = "폴더는 한 번에 20개까지 선택할 수 있어요. 다시 연결해 주세요."
            return
        }
        message.stringValue = "선택한 \(folders.count)개 폴더의 QWEN 지침을 준비하고 있어요…"
        installing = true
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                try self.connect(secret: secret, folders: folders)
                DispatchQueue.main.async {
                    let done = NSAlert()
                    done.messageText = "Mac 연결이 끝났어요"
                    done.informativeText = "선택한 \(folders.count)개 폴더에 정리 지침이 준비됐어요.\n모아 웹앱으로 돌아가면 다음 단계가 자동으로 표시됩니다."
                    done.addButton(withTitle: "확인")
                    done.runModal()
                    NSApp.terminate(nil)
                }
            } catch {
                DispatchQueue.main.async {
                    self.installing = false
                    self.message.stringValue = "연결하지 못했어요. 모아 웹앱에서 다시 시도해 주세요."
                    let failed = NSAlert()
                    failed.messageText = "Mac 연결 실패"
                    failed.informativeText = error.localizedDescription
                    failed.addButton(withTitle: "확인")
                    failed.runModal()
                }
            }
        }
    }

    func connect(secret: String, folders: [String]) throws {
        let keyURL = FileManager.default.homeDirectoryForCurrentUser
            .appendingPathComponent("Library/Application Support/Moa/local-key")
        let key = try String(contentsOf: keyURL, encoding: .utf8).trimmingCharacters(in: .whitespacesAndNewlines)
        guard !key.isEmpty else { throw NSError(domain: "MoaHelper", code: 1, userInfo: [NSLocalizedDescriptionKey: "Mac 연결 프로그램을 다시 설치해 주세요."]) }
        func currentCSRF() throws -> String {
            guard let value = try request("auth/session/")["csrf"] as? String else {
                throw NSError(domain: "MoaHelper", code: 2, userInfo: [NSLocalizedDescriptionKey: "로컬 보안 세션을 시작하지 못했어요."])
            }
            return value
        }
        _ = try request("local/unlock/", body: [:], csrf: currentCSRF(), localKey: key)
        _ = try request("local/folders/", body: ["folders": folders], csrf: currentCSRF())
        if let _ = try request("local/setup/")["cloud_origin"] as? String {
            _ = try request("local/cloud/disconnect/", body: [:], csrf: currentCSRF())
        }
        _ = try request("local/cloud/connect/", body: ["origin": origin, "pairing_secret": secret], csrf: currentCSRF())
        let deadline = Date().addingTimeInterval(3600)
        while Date() < deadline {
            let progress = try request("local/folders/")
            let state = progress["status"] as? String ?? "failed"
            if state == "completed" {
                _ = try request("local/setup/", body: [:], csrf: currentCSRF())
                return
            }
            if state == "failed" {
                throw NSError(domain: "MoaHelper", code: 4, userInfo: [NSLocalizedDescriptionKey: progress["detail"] as? String ?? "QWEN 지침을 다시 만들어 주세요."])
            }
            let completed = progress["completed"] as? Int ?? 0
            let folder = progress["folder"] as? String ?? ""
            DispatchQueue.main.async {
                self.message.stringValue = state == "generating"
                    ? "QWEN이 지침을 작성하고 있어요. \(completed + 1)/\(folders.count)\n\(folder)"
                    : "QWEN을 Mac에 준비하고 있어요. 처음에는 모델 다운로드로 시간이 걸릴 수 있어요."
            }
            Thread.sleep(forTimeInterval: 2)
        }
        throw NSError(domain: "MoaHelper", code: 5, userInfo: [NSLocalizedDescriptionKey: "지침 준비 시간이 오래 걸리고 있어요. 연결 앱에서 다시 확인해 주세요."])
    }

    func request(_ path: String, body: [String: Any]? = nil, csrf: String? = nil, localKey: String? = nil) throws -> [String: Any] {
        let url = URL(string: "http://127.0.0.1:8000/api/v1/" + path)!
        var request = URLRequest(url: url)
        request.timeoutInterval = 22
        if let body = body {
            request.httpMethod = "POST"
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        if let csrf = csrf { request.setValue(csrf, forHTTPHeaderField: "X-CSRFToken") }
        if let localKey = localKey { request.setValue(localKey, forHTTPHeaderField: "X-Moa-Local-Key") }
        let wait = DispatchSemaphore(value: 0)
        var result: Data?
        var response: URLResponse?
        var failure: Error?
        URLSession.shared.dataTask(with: request) { data, received, error in
            result = data; response = received; failure = error; wait.signal()
        }.resume()
        guard wait.wait(timeout: .now() + 24) == .success, let http = response as? HTTPURLResponse, let data = result else {
            throw failure ?? NSError(domain: "MoaHelper", code: 3, userInfo: [NSLocalizedDescriptionKey: "Mac 연결 프로그램이 실행 중인지 확인해 주세요."])
        }
        let payload = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] ?? [:]
        guard (200..<300).contains(http.statusCode) else {
            throw NSError(domain: "MoaHelper", code: http.statusCode,
                          userInfo: [NSLocalizedDescriptionKey: payload["detail"] as? String ?? "연결 요청을 완료하지 못했어요."])
        }
        return payload
    }
}
let app = NSApplication.shared
let delegate = HelperApp(); app.delegate = delegate; app.setActivationPolicy(.regular); app.run()
