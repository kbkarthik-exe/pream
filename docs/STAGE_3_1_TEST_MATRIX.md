# AICF Phase 3 — Stage 3.1 Test Matrix

This matrix documents all 81 regression and verification tests passing in AICF Phase 3 Stage 3.1.

| # | Suite | Test Name | Focus Area | Input Fixture | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|---|
| 1 | Stage 1 | `test_01_png_exif_ai_software_marker` | Metadata Attribution | PNG with `Software: Midjourney` | Attributed to Midjourney | MATCH | **PASS** |
| 2 | Stage 1 | `test_02_jpeg_dall_e_comment` | Metadata Attribution | JPEG with DALL-E comment marker | Attributed to DALL-E | MATCH | **PASS** |
| 3 | Stage 1 | `test_03_stable_diffusion_parameters` | Prompt Attribution | PNG with `parameters` metadata chunk | Prompt extracted, SD attributed | MATCH | **PASS** |
| 4 | Stage 1 | `test_04_adobe_firefly_c2pa_metadata` | C2PA Metadata | Adobe Firefly metadata markers | Firefly attributed | MATCH | **PASS** |
| 5 | Stage 1 | `test_05_clean_camera_jpeg_no_ai_provenance` | Natural Provenance | Canon EOS camera metadata | `UNKNOWN_OR_NATURAL` | MATCH | **PASS** |
| 6 | Stage 1 | `test_06_stripped_metadata_inconclusive` | Stripped Container | Image with zero metadata tags | `UNKNOWN_OR_NATURAL` | MATCH | **PASS** |
| 7 | Stage 1 | `test_07_flux_generator_attribution` | Diffusion Attribution | Black Forest Labs Flux signature | Attributed to Flux.1 | MATCH | **PASS** |
| 8 | Stage 1 | `test_08_comfyui_prompt_workflow_graph` | Node Graph Attribution | ComfyUI prompt/extra_data JSON | ComfyUI attributed | MATCH | **PASS** |
| 9 | Stage 1 | `test_09_bing_dall_e_3_user_comment` | Bing Attribution | Bing Image Creator UserComment | Attributed to Bing/DALL-E 3 | MATCH | **PASS** |
| 10 | Stage 1 | `test_10_google_imagen_provenance` | Imagen Attribution | Google Imagen SynthID/metadata marker | Attributed to Google Imagen | MATCH | **PASS** |
| 11 | Stage 1 | `test_11_multiple_conflicting_markers` | Conflict Resolution | Multiple mismatched tool signatures | Evidence conflict resolved safely | MATCH | **PASS** |
| 12 | Stage 1 | `test_12_attribution_schema_validation` | Schema Conformance | GeneratorAttributionResult fields | Valid Pydantic/dataclass schema | MATCH | **PASS** |
| 13 | Stage 2.4 | `test_01_png_c2pa_manifest_detected` | C2PA Provenance | PNG with C2PA manifest box | `MANIFEST_PARSED` | MATCH | **PASS** |
| 14 | Stage 2.4 | `test_02_jpeg_c2pa_app11_marker_detected` | C2PA Provenance | JPEG with APP11 marker | `MANIFEST_PARSED` | MATCH | **PASS** |
| 15 | Stage 2.4 | `test_03_webp_c2pa_chunk_detected` | C2PA Provenance | WebP with RIFF C2PA chunk | `MANIFEST_PARSED` | MATCH | **PASS** |
| 16 | Stage 2.4 | `test_04_no_manifest_returns_clean_status` | C2PA Provenance | Clean image without provenance | `NO_MANIFEST_PRESENT` | MATCH | **PASS** |
| 17 | Stage 2.4 | `test_05_c2pa_signature_distinguished_from_trust` | Trust Calibration | Untrusted root certificate | `SIGNATURE_VALID` / `CERT_UNTRUSTED` | MATCH | **PASS** |
| 18 | Stage 2.4 | `test_06_c2pa_asset_binding_unverified_rule` | Binding Hardening | Manifest marker present | `BINDING_UNVERIFIED` (Never VALID) | MATCH | **PASS** |
| 19 | Stage 2.4 | `test_07_metadata_camera_exif_analysis` | Metadata Forensics | Rich DSLR EXIF tags | Forensic camera indicators parsed | MATCH | **PASS** |
| 20 | Stage 2.4 | `test_08_metadata_editing_software_detected` | Metadata Forensics | Photoshop / GIMP software tag | Manipulation indicators recorded | MATCH | **PASS** |
| 21 | Stage 2.4 | `test_09_ela_spliced_region_detected` | Manipulation (ELA) | High-contrast resaved JPEG patch | Elevated error residual in patch | MATCH | **PASS** |
| 22 | Stage 2.4 | `test_10_ela_edge_damping_prevents_false_positive` | Manipulation (ELA) | High-frequency geometric edges | Edge mask damps ELA false alarms | MATCH | **PASS** |
| 23 | Stage 2.4 | `test_11_noise_residual_inconsistency` | Manipulation (Noise) | Spliced patch with foreign noise | Noise variance mismatch detected | MATCH | **PASS** |
| 24 | Stage 2.4 | `test_12_copy_move_block_matching` | Manipulation (CMFD) | Duplicated 64x64 pixel square | Spatial cluster match found | MATCH | **PASS** |
| 25 | Stage 2.4 | `test_13_copy_move_threshold_limits` | CMFD Coverage Limit | Image exceeding 4000 candidate blocks | Scaled down safely / bounds enforced | MATCH | **PASS** |
| 26 | Stage 2.4 | `test_14_frequency_fft_grid_artifacts` | Frequency Forensics | Up-sampling checkerboard artifact | Spectral peaks identified | MATCH | **PASS** |
| 27 | Stage 2.4 | `test_15_localization_bounding_boxes` | Tampering Localizer | Connected anomaly components | Bounding boxes & coverage computed | MATCH | **PASS** |
| 28 | Stage 2.4 | `test_16_decompression_bomb_rejected` | Security Hardening | 10000x10000 crafted PNG IHDR | `CONTAINER_SECURITY` rejection | MATCH | **PASS** |
| 29 | Stage 2.4 | `test_17_oversized_single_axis_rejection` | Security Hardening | 9000px single axis PNG | `AXIS_LIMIT_EXCEEDED` rejection | MATCH | **PASS** |
| 30 | Stage 2.4 | `test_18_repetitive_natural_textures_no_false_copy_move` | False-Positive Defense | Brick wall repetitive texture | No false CMFD tampering alarm | MATCH | **PASS** |
| 31 | Stage 2.4 | `test_19_heavy_jpeg_compression_does_not_trigger_splicing` | False-Positive Defense | Q=20 compressed image | Quality-adjusted thresholds apply | MATCH | **PASS** |
| 32 | Stage 2.4 | `test_20_low_contrast_natural_scene` | False-Positive Defense | Foggy low-contrast landscape | Clean result without false alarms | MATCH | **PASS** |
| 33 | Stage 2.4 | `test_21_evidence_fusion_two_dimensional_verdict` | Architecture Fusion | Independent AI + tampering runs | 2 distinct verdict dimensions | MATCH | **PASS** |
| 34 | Stage 2.4 | `test_22_evidence_fusion_uncalibrated_heuristic_confidence` | Calibration Labeling | Fusion report confidence output | Labeled `HEURISTIC_SCORE` | MATCH | **PASS** |
| 35 | Stage 2.4 | `test_23_performance_benchmark_under_two_seconds` | Latency Benchmark | 512x512 complex test fixture | Total pipeline < 2.0s | MATCH | **PASS** |
| 36 | Stage 2.4 | `test_24_c2pa_status_schema_immutability` | Schema Integrity | Enum definitions | `BINDING_UNVERIFIED` present | MATCH | **PASS** |
| 37 | Stage 2.4 | `test_25_unsupported_image_container_rejected` | Container Validation | TIFF/BMP unsupported format | Graceful rejection | MATCH | **PASS** |
| 38 | Stage 2.4 | `test_26_corrupted_exif_header_handled_gracefully` | Resilience | Corrupted EXIF IFD pointer | Catches exception safely | MATCH | **PASS** |
| 39 | Stage 2.4 | `test_27_truncated_c2pa_manifest_handled` | Resilience | Incomplete C2PA segment | Catches truncation safely | MATCH | **PASS** |
| 40 | Stage 2.4 | `test_28_evidence_strength_ordering` | Telemetry Scoring | Fusion evidence weighing | Evidence strength sorted properly | MATCH | **PASS** |
| 41 | Baseline | `test_image_analysis_unauthenticated` | API Auth Gate | POST /analyze without session | HTTP 401 Unauthorized | MATCH | **PASS** |
| 42 | Baseline | `test_image_analysis_empty_upload` | API Ingestion | 0-byte file upload | HTTP 422 ("empty") | MATCH | **PASS** |
| 43 | Baseline | `test_image_analysis_corrupted_file` | API Ingestion | Corrupted JPEG header stream | HTTP 422 ("corrupted") | MATCH | **PASS** |
| 44 | Baseline | `test_image_analysis_unsupported_format` | API Ingestion | Text file disguised as PNG | HTTP 422 ("unsupported"/"corrupted") | MATCH | **PASS** |
| 45 | Baseline | `test_image_analysis_oversized_file` | API Ingestion | File exceeding byte threshold | HTTP 422 ("exceeds maximum") | MATCH | **PASS** |
| 46 | Baseline | `test_image_analysis_excessive_dimensions` | API Ingestion | Image exceeding pixel threshold | HTTP 422 ("exceeds") | MATCH | **PASS** |
| 47 | Baseline | `test_image_analysis_valid_jpeg` | Production Inference | Real 128x128 JPEG | HTTP 200, Swin+ViT inference | MATCH | **PASS** |
| 48 | Baseline | `test_image_analysis_valid_png` | Production Inference | Real 128x128 PNG | HTTP 200, Swin+ViT inference | MATCH | **PASS** |
| 49 | Baseline | `test_image_analysis_valid_webp` | Production Inference | Real 128x128 WebP | HTTP 200, Swin+ViT inference | MATCH | **PASS** |
| 50 | Baseline | `test_image_analysis_low_resolution_inconclusive` | Baseline Logic | 16x16 thumbnail | `INCONCLUSIVE` classification | MATCH | **PASS** |
| 51 | Baseline | `test_image_analysis_model_unavailable` | Fault Tolerance | Model load failure simulation | HTTP 503 / graceful degradation | MATCH | **PASS** |
| 52 | Baseline | `test_image_analysis_inference_exception` | Fault Tolerance | Inference runtime error | HTTP 500 / structured error | MATCH | **PASS** |
| 53 | Baseline | `test_image_analysis_user_isolation` | Security / Access | Analyst B accesses Analyst A record | HTTP 403 Forbidden | MATCH | **PASS** |
| 54 | Baseline | `test_image_analysis_history_and_case_save` | Persistence | Analysis saved to history and cases | Record queryable in history | MATCH | **PASS** |
| 55 | Baseline | `test_image_analysis_no_temp_file_leak` | Resource Safety | Full upload-to-inference pipeline | Zero temporary files on disk | MATCH | **PASS** |
| 56 | Baseline | `test_image_analysis_ensemble_calibration` | Algorithm Integrity | Temperature scaling & covariance | Ensemble score calibrated | MATCH | **PASS** |
| 57 | Baseline | `test_image_analysis_secondary_vit_execution` | Ensemble Engine | ViT secondary model prediction | ViT outputs score cleanly | MATCH | **PASS** |
| 58 | Baseline | `test_image_analysis_ela_explainability_heatmap` | Heatmap Generator | ELA grayscale and colored heatmaps | Valid data URLs generated | MATCH | **PASS** |
| 59 | Baseline | `test_image_analysis_multi_detector_api_response` | Schema Response | Response contains detector_scores | Structured response conforms | MATCH | **PASS** |
| 60 | Baseline | `test_image_analysis_pdf_with_ensemble` | PDF Service | PDF generated with ensemble data | Valid binary PDF returned | MATCH | **PASS** |
| 61 | Baseline | `test_image_analysis_hive_cloud_adapter_unconfigured` | Cloud Adapter | Unset Hive API credentials | Graceful fallback to local | MATCH | **PASS** |
| 62 | Stage 3.1 | `test_01_valid_jpeg_ingestion_reaches_detector` | Ingestion Gate | Valid 64x64 JPEG + Mock detector | HTTP 200; detector invoked once | MATCH | **PASS** |
| 63 | Stage 3.1 | `test_02_valid_png_ingestion_reaches_detector` | Ingestion Gate | Valid 64x64 PNG + Mock detector | HTTP 200; detector invoked once | MATCH | **PASS** |
| 64 | Stage 3.1 | `test_03_valid_webp_reaches_detector` | Ingestion Gate | Valid 64x64 WebP + Mock detector | HTTP 200; detector invoked once | MATCH | **PASS** |
| 65 | Stage 3.1 | `test_04_empty_file_rejected_before_detector` | Ingestion Gate | 0-byte upload | HTTP 422; detector NOT invoked | MATCH | **PASS** |
| 66 | Stage 3.1 | `test_05_oversized_upload_rejected_before_detector` | Ingestion Gate | 500 B limit + 1 KB image | HTTP 422; detector NOT invoked | MATCH | **PASS** |
| 67 | Stage 3.1 | `test_06_fake_jpeg_disguised_text_rejected` | Ingestion Gate | Text file named `payload.jpg` | HTTP 422; detector NOT invoked | MATCH | **PASS** |
| 68 | Stage 3.1 | `test_07_fake_png_disguised_garbage_rejected` | Ingestion Gate | Random binary named `exploit.png` | HTTP 422; detector NOT invoked | MATCH | **PASS** |
| 69 | Stage 3.1 | `test_08_mime_type_mismatch_validated_by_content` | Ingestion Gate | Client sends JPEG with `image/png` | HTTP 200; parsed by signature | MATCH | **PASS** |
| 70 | Stage 3.1 | `test_09_extension_mismatch_validated_by_content` | Ingestion Gate | Client sends PNG named `photo.jpg` | HTTP 200; parsed by signature | MATCH | **PASS** |
| 71 | Stage 3.1 | `test_10_truncated_jpeg_stream_rejected` | Ingestion Gate | JPEG SOI + truncated 8 bytes | HTTP 422; detector NOT invoked | MATCH | **PASS** |
| 72 | Stage 3.1 | `test_11_corrupted_raster_body_rejected` | Ingestion Gate | Valid SOI + corrupted body chunks | HTTP 422; detector NOT invoked | MATCH | **PASS** |
| 73 | Stage 3.1 | `test_12_decompression_bomb_pre_decode_ihdr_rejected` | Ingestion Gate | 10000x10000 PNG IHDR (60 bytes) | HTTP 422 pre-decode; no raster alloc | MATCH | **PASS** |
| 74 | Stage 3.1 | `test_13_excessive_single_axis_width_rejected` | Ingestion Gate | 9000x100 PNG | HTTP 422; axis threshold enforced | MATCH | **PASS** |
| 75 | Stage 3.1 | `test_14_excessive_single_axis_height_rejected` | Ingestion Gate | 100x9000 PNG | HTTP 422; axis threshold enforced | MATCH | **PASS** |
| 76 | Stage 3.1 | `test_15_rejection_responses_contain_no_memory_addresses` | Leak Prevention | Malformed upload error body | No hex memory pointers (`0x...`) | MATCH | **PASS** |
| 77 | Stage 3.1 | `test_16_rejection_responses_contain_no_internal_paths` | Leak Prevention | Malformed upload error body | No server paths (`C:\`, `app`) | MATCH | **PASS** |
| 78 | Stage 3.1 | `test_17_no_temp_file_leakage_after_rejection` | Resource Safety | Rejected upload attempt | 0 temp files leaked | MATCH | **PASS** |
| 79 | Stage 3.1 | `test_18_unit_pre_decode_dimension_sniffing` | Unit Sniffer | PNG, JPEG, WebP pre-decode sniff | Unpacked w, h, fmt without Pillow | MATCH | **PASS** |
| 80 | Stage 3.1 | `test_19_unit_validate_image_security_telemetry_statuses` | Unit Engine | Safe, bomb, axis, empty inputs | Exact telemetry status codes | MATCH | **PASS** |
| 81 | Stage 3.1 | `test_20_unit_unsupported_format_rejection` | Unit Engine | GIF format test stream | `UNSUPPORTED_FORMAT` status | MATCH | **PASS** |
