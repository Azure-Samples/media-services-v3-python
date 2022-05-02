// First we create a TransformOutput
let transformOutput: TransformOutput[] = [
    {
        preset: factory.createBuiltInStandardEncoderPreset({
            presetName: "SaasSourceAligned360pOnly" // There are some undocumented magical presets in our toolbox that do fun stuff - this one is going to copy the codecs from the source and also generate a 360p proxy file.
            
            // Other magical presets to play around with, that might (or might not) work for your source video content...
            // "SaasCopyCodec" - this just copies the source video and audio into an MP4 ready for streaming.  The source has to be H264 and AAC with CBR encoding and no B frames typically. 
            // "SaasProxyCopyCodec" - this copies the source video and audio into an MP4 ready for streaming and generates a proxy file.   The source has to be H264 and AAC with CBR encoding and no B frames typically. 
            // "SaasSourceAligned360pOnly" - same as above, but generates a single 360P proxy layer that is aligned in GOP to the source file. Useful for "back filling" a proxy on a pre-encoded file uploaded.  
            // "SaasSourceAligned540pOnly"-  generates a single 540P proxy layer that is aligned in GOP to the source file. Useful for "back filling" a proxy on a pre-encoded file uploaded. 
            // "SaasSourceAligned540p" - generates an adaptive set of 540P and 360P that is aligned to the source file. used for "back filling" a pre-encoded or uploaded source file in an output asset for better streaming. 
            // "SaasSourceAligned360p" - generates an adaptive set of 360P and 180P that is aligned to the source file. used for "back filling" a pre-encoded or uploaded source file in an output asset for better streaming. 
        })
    },
    {
    // uses the Standard Encoder Preset to generate copy the source audio and video to an output track, and generate a proxy and a sprite
    preset: factory.createStandardEncoderPreset({
        codecs: [
            factory.createCopyVideo({  // this part of the sample is a custom copy codec - It will copy the source video track directly to the output MP4 file
            }),
            factory.createCopyAudio({ // this part of the sample is a custom copy codec - copies the audio track from the source to the output MP4 file
            }),
            factory.createJpgImage({
                // Also generate a set of thumbnails in one Jpg file (thumbnail sprite)
                start: "0%",
                step: "5%",
                range: "100%",
                spriteColumn:10,  // Key is to set the column number here, and then set the width and height of the layer.
                layers: [
                    factory.createJpgLayer({
                        width: "20%",
                        height: "20%",
                        quality:85
                    })
                ]
            })
        ],
        // Specify the format for the output files - one for video+audio, and another for the thumbnails
        formats: [
            // Mux the H.264 video and AAC audio into MP4 files, using basename, label, bitrate and extension macros
            // Note that since you have multiple H264Layers defined above, you have to use a macro that produces unique names per H264Layer
            // Either {Label} or {Bitrate} should suffice
            factory.createMp4Format({
                filenamePattern: "CopyCodec-{Basename}{Extension}"
            }),
            factory.createJpgFormat({
                filenamePattern: "sprite-{Basename}-{Index}{Extension}"
            })
        ]
    }),
    // What should we do with the job if there is an error?
    onError: KnownOnErrorType.StopProcessingJob,
    // What is the relative priority of this job to others? Normal, high or low?
    relativePriority: KnownPriority.Normal
}
];
