import AppKit
import Combine
import SwiftUI

struct AssistantSessionSnapshot: Equatable, Sendable {
    var provider: String
    var sessionId: String
}

func assistantSessionCanFork(provider: String) -> Bool {
    provider.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() == "codex"
}

enum AssistantSessionHeaderAction: Equatable {
    case copy
    case fork
}

@MainActor
final class TitlebarAssistantSessionModel: ObservableObject {
    @Published private(set) var session: AssistantSessionSnapshot?

    private weak var observedTabManager: TabManager?
    private weak var observedWorkspace: Workspace?
    private var selectedTabCancellable: AnyCancellable?
    private var workspaceSessionCancellable: AnyCancellable?
    private var refreshCancellables: Set<AnyCancellable> = []

    func bind(to tabManager: TabManager) {
        if observedTabManager !== tabManager {
            observedTabManager = tabManager
            selectedTabCancellable = tabManager.$selectedTabId
                .receive(on: RunLoop.main)
                .sink { [weak self] _ in
                    self?.attachWorkspace()
                    self?.refresh()
                }
        }

        attachWorkspace()
        installFocusObserverIfNeeded()
        refresh()
    }

    func refresh() {
        session = observedTabManager?.selectedWorkspace?.activeAssistantSession()
    }

    private func attachWorkspace() {
        let workspace = observedTabManager?.selectedWorkspace
        guard observedWorkspace !== workspace else { return }

        observedWorkspace = workspace
        workspaceSessionCancellable = workspace?.$panelAssistantSessions
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in
                self?.refresh()
            }
    }

    private func installFocusObserverIfNeeded() {
        guard refreshCancellables.isEmpty else { return }
        let center = NotificationCenter.default
        [
            Notification.Name.ghosttyDidFocusSurface,
            .ghosttyDidFocusTab,
            .browserDidBecomeFirstResponderWebView,
            .browserDidFocusAddressBar,
        ].forEach { name in
            center.publisher(for: name)
                .receive(on: RunLoop.main)
                .sink { [weak self] _ in
                    self?.refresh()
                }
                .store(in: &refreshCancellables)
        }
    }
}

struct AssistantSessionHeaderButton: NSViewRepresentable {
    let session: AssistantSessionSnapshot
    let actionHandler: (AssistantSessionHeaderAction) -> Void

    func makeNSView(context: Context) -> AssistantSessionButton {
        let button = AssistantSessionButton()
        button.actionHandler = actionHandler
        button.update(session: session)
        return button
    }

    func updateNSView(_ nsView: AssistantSessionButton, context: Context) {
        nsView.actionHandler = actionHandler
        nsView.update(session: session)
    }
}

final class AssistantSessionButton: NSButton {
    var actionHandler: ((AssistantSessionHeaderAction) -> Void)?
    private var session: AssistantSessionSnapshot?

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        isBordered = false
        focusRingType = .none
        bezelStyle = .regularSquare
        setButtonType(.momentaryChange)
        wantsLayer = true
        layer?.cornerRadius = 6
        layer?.masksToBounds = true
        imagePosition = .imageOnly
        font = .monospacedSystemFont(ofSize: 10, weight: .medium)
        lineBreakMode = .byTruncatingMiddle
        contentTintColor = .secondaryLabelColor
        translatesAutoresizingMaskIntoConstraints = false
        setContentHuggingPriority(.defaultLow, for: .horizontal)
        setContentCompressionResistancePriority(.defaultLow, for: .horizontal)
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override var mouseDownCanMoveWindow: Bool { false }

    override func acceptsFirstMouse(for event: NSEvent?) -> Bool {
        true
    }

    override func mouseDown(with event: NSEvent) {
        guard let session else { return }
        let shouldFork = assistantSessionCanFork(provider: session.provider) &&
            event.modifierFlags.intersection(.deviceIndependentFlagsMask).contains(.command)
        actionHandler?(shouldFork ? .fork : .copy)
    }

    override func accessibilityPerformPress() -> Bool {
        actionHandler?(.copy)
        return true
    }

    func update(session: AssistantSessionSnapshot) {
        self.session = session
        title = session.sessionId
        font = .monospacedSystemFont(ofSize: 10, weight: .medium)
        lineBreakMode = .byTruncatingMiddle
        contentTintColor = .secondaryLabelColor
        toolTip = assistantSessionCanFork(provider: session.provider)
            ? "Click to copy. Command-click to fork."
            : "Click to copy."
        setAccessibilityLabel("Current assistant session ID")
        setAccessibilityIdentifier("titlebarControl.assistantSession")
        setAccessibilityValue(session.sessionId)
        layer?.backgroundColor = NSColor.secondaryLabelColor.withAlphaComponent(0.08).cgColor
    }

    override var intrinsicContentSize: NSSize {
        let base = super.intrinsicContentSize
        return NSSize(width: min(340, base.width + 16), height: max(22, base.height + 6))
    }
}
