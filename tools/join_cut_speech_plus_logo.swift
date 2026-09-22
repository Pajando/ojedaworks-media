import AVFoundation
import Foundation

// usage: join2 speech.mp4 logo.mp4 out.mp4 videoCutSeconds audioEndSeconds
let a = CommandLine.arguments
guard a.count == 6, let vCut = Double(a[4]), let aEnd = Double(a[5]) else { print("usage: join2 speech logo out vCut aEnd"); exit(2) }
let speech = AVURLAsset(url: URL(fileURLWithPath: a[1]))
let logo = AVURLAsset(url: URL(fileURLWithPath: a[2]))
let out = URL(fileURLWithPath: a[3])
try? FileManager.default.removeItem(at: out)
let comp = AVMutableComposition()
let vTrack = comp.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid)!
let aTrack = comp.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)!
let sem = DispatchSemaphore(value: 0)
Task {
    do {
        let ts: Int32 = 600
        let vc = CMTime(seconds: vCut, preferredTimescale: ts)
        let ae = CMTime(seconds: aEnd, preferredTimescale: ts)
        let sv = try await speech.loadTracks(withMediaType: .video).first!
        let sa = try await speech.loadTracks(withMediaType: .audio).first!
        let lv = try await logo.loadTracks(withMediaType: .video).first!
        let ld = try await logo.load(.duration)
        try vTrack.insertTimeRange(CMTimeRange(start: .zero, duration: vc), of: sv, at: .zero)
        try vTrack.insertTimeRange(CMTimeRange(start: .zero, duration: ld), of: lv, at: vc)
        try aTrack.insertTimeRange(CMTimeRange(start: .zero, duration: ae), of: sa, at: .zero)
        print("video = speech[0..\(vCut)] + logo[0..\(ld.seconds)]  total \(CMTimeAdd(vc, ld).seconds)s; audio = speech[0..\(aEnd)]")
    } catch { print("error: \(error)"); exit(1) }
    sem.signal()
}
sem.wait()
guard let exp = AVAssetExportSession(asset: comp, presetName: AVAssetExportPresetHighestQuality) else { print("no export session"); exit(1) }
exp.outputURL = out; exp.outputFileType = .mp4; exp.shouldOptimizeForNetworkUse = true
exp.exportAsynchronously { sem.signal() }
sem.wait()
print("export status=\(exp.status.rawValue)")
