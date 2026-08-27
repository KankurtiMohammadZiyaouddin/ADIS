export default function ImageForensicsPage() {
  return (
    <main className="flex-1 overflow-auto bg-background p-gutter flex gap-gutter">
      {/* Center Canvas: Image Comparison */}
      <div className="flex-1 flex flex-col gap-gutter min-w-0">
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg flex-1 flex flex-col overflow-hidden">
          <div className="h-10 border-b border-outline-variant bg-surface-container flex items-center justify-between px-4 shrink-0">
            <span className="text-label-md text-on-surface">Analysis Canvas: EV-882.jpg</span>
            <div className="flex items-center gap-2">
              <button className="p-1 hover:bg-surface-container-highest rounded text-on-surface-variant"><span className="material-symbols-outlined" style={{fontSize: 18}}>zoom_in</span></button>
              <button className="p-1 hover:bg-surface-container-highest rounded text-on-surface-variant"><span className="material-symbols-outlined" style={{fontSize: 18}}>zoom_out</span></button>
              <button className="p-1 hover:bg-surface-container-highest rounded text-on-surface-variant"><span className="material-symbols-outlined" style={{fontSize: 18}}>center_focus_strong</span></button>
            </div>
          </div>
          <div className="flex-1 flex gap-4 p-4 min-h-0 bg-surface">
            {/* Original Image with Bounding Box */}
            <div className="flex-1 flex flex-col border border-outline-variant rounded bg-surface-container-lowest relative overflow-hidden group">
              <div className="absolute top-2 left-2 bg-on-surface/80 text-surface-container-lowest px-2 py-1 rounded text-label-sm z-10">Original (Suspect Region)</div>
              <img className="w-full h-full object-contain p-2" data-alt="A high-resolution photograph of an urban street scene during daytime. The scene includes pedestrians, a parked car, and shop storefronts. A specific rectangular region near the parked car is highlighted with a bright red bounding box to indicate a suspicious area under forensic investigation. The image is clean, sharp, and typical of digital evidence gathered from a smartphone or CCTV camera." src="https://lh3.googleusercontent.com/aida-public/AB6AXuAzghDlgaeyUL8F-vm52pY9Frqo-u2hE9ogT3KknCYBy78a-EJPq9K-QTQUCwrUGyLd1QXKenueYYy622vx9HxqcbLK8dcU9uZfSgjcEFfaKg4mwdB1xMBB8rl-dB6N95Tq8_3DMG2hNhN6UjO4FmOiSwkxoSUGHk2mlrEEf7yiwd3pWc17pwib-t8GLYBMEQlz38byJI4GDdb_-iNxIcqPP8BuFEjd3VyQ3FOQixY3NK6DzcEQuTk" />
              {/* Suspicious Bounding Box Simulation */}
              <div className="absolute border-2 border-error w-32 h-32 top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-error/10 hidden group-hover:block transition-all" />
            </div>
            {/* Forensic Heatmap */}
            <div className="flex-1 flex flex-col border border-outline-variant rounded bg-surface-container-lowest relative overflow-hidden">
              <div className="absolute top-2 left-2 bg-on-surface/80 text-surface-container-lowest px-2 py-1 rounded text-label-sm z-10">Error Level Analysis (ELA)</div>
              <img className="w-full h-full object-contain p-2 filter contrast-125 saturate-150" data-alt="A highly technical error level analysis (ELA) heat map of the corresponding urban street scene. The overall image is dark, mostly black and deep purple, representing areas of uniform compression. The previously highlighted rectangular region near the parked car glows intensely with bright white, yellow, and red pixels, clearly indicating a high level of manipulation or localized compression inconsistency indicative of digital tampering." src="https://lh3.googleusercontent.com/aida-public/AB6AXuDLVuqNBofXi32qvbqusPM2RQhejmfFdnCWY48Cz5tqg4jb7coYHLIYMHJd6dHuBqoacebjPD0IjH47Ovga7AmXWRAQYIYoLtcWDHQGotI9rTu2tcWeWk5eBNW2R_c29QzHSzeKo9vAh50rLSSnLVCWI8fmxUN0ngzhaxJ-CJLsEqDooQ7as95fJ_gAjr1ooEytqcvKuvFqBHcx2jQlnl3jeiTIfEZbHEh6NfZ7uuZyU8JJiaF2h-A" />
            </div>
          </div>
        </div>
        {/* Secondary Panel: Metadata & Timeline */}
        <div className="h-48 flex gap-gutter shrink-0">
          <div className="flex-1 bg-surface-container-lowest border border-outline-variant rounded-lg flex flex-col overflow-hidden">
            <div className="h-8 border-b border-outline-variant bg-surface-container flex items-center px-4 text-label-md text-on-surface">
              EXIF / Metadata Summary
            </div>
            <div className="p-3 overflow-y-auto">
              <table className="w-full text-body-sm font-body-sm text-left">
                <tbody>
                  <tr className="border-b border-surface-variant">
                    <th className="py-1 text-on-surface-variant font-medium w-1/3">Camera Model</th>
                    <td className="py-1 text-on-surface">iPhone 13 Pro</td>
                  </tr>
                  <tr className="border-b border-surface-variant">
                    <th className="py-1 text-on-surface-variant font-medium">Software</th>
                    <td className="py-1 text-error font-medium">Adobe Photoshop 2023 (Flagged)</td>
                  </tr>
                  <tr className="border-b border-surface-variant">
                    <th className="py-1 text-on-surface-variant font-medium">Date/Time Original</th>
                    <td className="py-1 text-on-surface">2023-10-24 14:32:11</td>
                  </tr>
                  <tr>
                    <th className="py-1 text-on-surface-variant font-medium">GPS Location</th>
                    <td className="py-1 text-on-surface">34.0522° N, 118.2437° W</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      {/* Right Sidebar: Analysis Panel */}
      <div className="w-80 flex flex-col gap-gutter shrink-0">
        {/* Probability Card */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-4">
          <h3 className="text-headline-sm font-headline-sm text-on-surface mb-4">Forensic Assessment</h3>
          <div className="mb-6">
            <div className="flex justify-between items-end mb-1">
              <span className="text-label-md text-on-surface-variant">Manipulation Probability</span>
              <span className="text-title-lg font-title-lg text-error">87%</span>
            </div>
            <div className="w-full bg-surface-variant rounded-full h-1.5">
              <div className="bg-error h-1.5 rounded-full" style={{width: '87%'}} />
            </div>
          </div>
          <div className="mb-4">
            <div className="flex justify-between items-end mb-1">
              <span className="text-label-md text-on-surface-variant">Model Confidence</span>
              <span className="text-body-md font-body-md text-primary">84%</span>
            </div>
            <div className="w-full bg-surface-variant rounded-full h-1">
              <div className="bg-primary h-1 rounded-full" style={{width: '84%'}} />
            </div>
          </div>
          <div className="space-y-2 mt-4">
            <h4 className="text-label-sm text-on-surface-variant uppercase tracking-wider">Detected Anomalies</h4>
            <div className="flex items-start gap-2 bg-error-container/20 p-2 rounded border border-error-container">
              <span className="material-symbols-outlined text-error" style={{fontSize: 16}}>warning</span>
              <div className="text-body-sm font-body-sm text-on-surface">
                <span className="font-semibold block text-error">Compression Artifacts</span>
                Localized grid inconsistencies detected at region [X:440, Y:210].
              </div>
            </div>
            <div className="flex items-start gap-2 bg-error-container/20 p-2 rounded border border-error-container">
              <span className="material-symbols-outlined text-error" style={{fontSize: 16}}>noise_aware</span>
              <div className="text-body-sm font-body-sm text-on-surface">
                <span className="font-semibold block text-error">Noise Inconsistency</span>
                Variance in sensor noise pattern indicates splicing.
              </div>
            </div>
          </div>
        </div>
        {/* Face Analysis (AI Action) */}
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-4 flex-1">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-label-md text-on-surface font-semibold">Face Extraction</h3>
            <button className="bg-secondary text-on-secondary px-3 py-1 rounded text-label-sm hover:opacity-90 transition-opacity">Run Deepfake Scan</button>
          </div>
          <div className="space-y-3">
            <div className="flex gap-3 items-center p-2 border border-outline-variant rounded bg-surface">
              <img className="w-12 h-12 rounded object-cover" data-alt="A tight cropped square image of a person's face extracted from a larger scene. The face is slightly blurry but discernible, showing a male subject with neutral expression. The lighting on the face appears slightly unnatural compared to the background, suggesting potential digital alteration or face-swapping." src="https://lh3.googleusercontent.com/aida-public/AB6AXuDu8kGNsvnLRk9MTWpCqWpMjdD6jj6GT_4Q3-EaKl4JU9rSrgaOVQVB3X9DIstFZ9xEhs3wuYrWJrih21PF7MRyCRNCm_R2ixmqO86YnLUWWkWJ3B2-HuRI0RlbF8b7xky52fsZr8QBkHuMKgXGLZX7f7ItiYpBcdMK5CDG1fvutpleemMVboBpQ8xGD1O1yWKSBiFmJBdGIwObnhTbG-kp_apuahpGPBTpGrPDqVHMzICufa3M-G4" />
              <div className="flex-1">
                <div className="text-body-sm font-body-sm text-on-surface font-medium">Subject 1 (Target)</div>
                <div className="text-label-sm text-on-surface-variant">Confidence: Medium</div>
              </div>
              <span className="material-symbols-outlined text-outline">more_vert</span>
            </div>
            <div className="flex gap-3 items-center p-2 border border-outline-variant rounded bg-surface">
              <div className="w-12 h-12 rounded bg-surface-variant flex items-center justify-center text-outline">
                <span className="material-symbols-outlined">person_search</span>
              </div>
              <div className="flex-1">
                <div className="text-body-sm font-body-sm text-on-surface font-medium">No other faces detected</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

