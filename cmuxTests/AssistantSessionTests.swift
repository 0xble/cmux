import XCTest

#if canImport(cmux_DEV)
@testable import cmux_DEV
#elseif canImport(cmux)
@testable import cmux
#endif

final class AssistantSessionTests: XCTestCase {
  func testAssistantSessionCanForkOnlyCodex() {
        XCTAssertTrue(assistantSessionCanFork(provider: "codex"))
        XCTAssertTrue(assistantSessionCanFork(provider: " CODEX "))
        XCTAssertFalse(assistantSessionCanFork(provider: "claude"))
        XCTAssertFalse(assistantSessionCanFork(provider: ""))
  }

  @MainActor
  func testPruneSurfaceMetadataRemovesAssistantSessionsForMissingPanels() {
    let workspace = Workspace()
        let keep = UUID()
        let drop = UUID()

        workspace.panelAssistantSessions = [
            keep: AssistantSessionSnapshot(provider: "codex", sessionId: "keep-id"),
            drop: AssistantSessionSnapshot(provider: "claude", sessionId: "drop-id"),
        ]

        workspace.pruneSurfaceMetadata(validSurfaceIds: [keep])

        XCTAssertEqual(
            workspace.panelAssistantSessions,
            [keep: AssistantSessionSnapshot(provider: "codex", sessionId: "keep-id")]
        )
    }
}
