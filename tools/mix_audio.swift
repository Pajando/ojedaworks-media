import AVFoundation
import Foundation

// usage: mix video.mp4 music.mp3 out.mp4 [musicVolumeDuringSpeech] [musicVolumeOutro] [speechEndSeconds]
let a = CommandLine.arguments
guard a.count >= 4 else { print("usage: mix video music out [volDuringSpeech] [volOutro] [speechEnd]"); exit(2) }
let videoURL = URL(fileURLWithPath: a[1])
let musicURL = URL(fileURLWithPath: a[2])
let outURL = URL(fileURLWithPath: a[3])
let volSpeech: Float = a.count > 4 ? Float(a[4])! : 0.10
let volOutro: Float = a.count > 5 ? Float(a[5])! : 0.35
try? FileManager.default.removeItem(at: outURL)

let videoAsset = AVURLAsset(url: videoURL)
let musicAsset = AVURLAsset(url: musicURL)
let comp = AVMutableComposition()
let vTrack = comp.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid)!
let speechTrack = comp.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)!
let musicTrack = comp.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)!

let sem = DispatchSemaphore(value: 0)
var videoDuration = CMTime.zero
var renderSize = CGSize(width: 720, height: 1280)
var videoTransform = CGAffineTransform.identity

Task {
    do {
        let vDur = try await videoAsset.load(.duration)
        videoDuration = vDur
        let v = try await videoAsset.loadTracks(withMediaType: .video).first!
        let vAudio = try await videoAsset.loadTracks(withMediaType: .audio).first
        renderSize = try await v.load(.naturalSize)
        videoTransform = try await v.load(.preferredTransform)
        try vTrack.insertTimeRange(CMTimeRange(start: .zero, duration: vDur), of: v, at: .zero)
        vTrack.preferredTransform = videoTransform
        if let vAudio = vAudio {
            try speechTrack.insertTimeRange(CMTimeRange(start: .zero, duration: vDur), of: vAudio, at: .zero)
        }
        let mDur = try await musicAsset.load(.duration)
        let m = try await musicAsset.loadTracks(withMediaType: .audio).first!
        // loop/trim music to cover the whole video duration
        var placed = CMTime.zero
        while placed < vDur {
            let remaining = CMTimeSubtract(vDur, placed)
            let take = CMTimeMinimum(mDur, remaining)
            try musicTrack.insertTimeRange(CMTimeRange(start: .zero, duration: take), of: m, at: placed)
            placed = CMTimeAdd(placed, take)
        }
    } catch { print("load error: \(error)"); exit(1) }
    sem.signal()
}
sem.wait()

// Audio mix: speech at full volume; music ducked under speech, swelling for last ~1s (the logo tail)
let audioMix = AVMutableAudioMix()
let speechParams = AVMutableAudioMixInputParameters(track: speechTrack)
speechParams.setVolume(1.0, at: .zero)
let musicParams = AVMutableAudioMixInputParameters(track: musicTrack)
let fadeInEnd = CMTime(seconds: 0.6, preferredTimescale: 600)
let swellStart = CMTimeSubtract(videoDuration, CMTime(seconds: 1.2, preferredTimescale: 600))
musicParams.setVolumeRamp(fromStartVolume: 0.0, toEndVolume: volSpeech, timeRange: CMTimeRange(start: .zero, duration: fadeInEnd))
musicParams.setVolume(volSpeech, at: fadeInEnd)
musicParams.setVolumeRamp(fromStartVolume: volSpeech, toEndVolume: volOutro, timeRange: CMTimeRange(start: swellStart, duration: CMTimeSubtract(videoDuration, swellStart)))
audioMix.inputParameters = [speechParams, musicParams]

guard let exp = AVAssetExportSession(asset: comp, presetName: AVAssetExportPresetHighestQuality) else { print("no export session"); exit(1) }
exp.outputURL = outURL
exp.outputFileType = .mp4
exp.audioMix = audioMix
exp.shouldOptimizeForNetworkUse = true
exp.exportAsynchronously { sem.signal() }
sem.wait()
print("export status=\(exp.status.rawValue) error=\(String(describing: exp.error)) duration=\(videoDuration.seconds)s")
