# Implementation Plan: AI Voice Order Confirmation System

## Overview

This implementation plan breaks down the AI Voice Order Confirmation System into manageable tasks following a logical build order: infrastructure setup → core pipeline modules → supporting modules → integration → testing → deployment. The system uses Python as the primary implementation language with an event-driven architecture built on Redis Pub/Sub.

The implementation follows these principles:
- Build infrastructure first (Event Bus, databases, storage)
- Implement core pipeline modules in processing order (Telephony → Audio → STT → LLM → State → TTS)
- Add supporting modules (Dashboard, Call Controller, Session Store, Logger)
- Integrate and test end-to-end flows
- Deploy with monitoring and observability

## Tasks

### Phase 1: Infrastructure Setup

- [-] 1. Set up project structure and core infrastructure
  - [x] 1.1 Initialize Python project with virtual environment and dependencies
    - Create project directory structure: `src/`, `tests/`, `config/`, `scripts/`
    - Set up `pyproject.toml` with dependencies: redis, psycopg2, boto3, fastapi, websockets, hypothesis
    - Create `.env.example` for configuration template
    - _Requirements: 11.1, 15.1_

  - [x] 1.2 Implement Event Bus core with Redis Pub/Sub
    - Create `src/event_bus/event_bus.py` with publish/subscribe methods
    - Implement Event Envelope validation with required fields (event_id, event_type, timestamp, source_module, session_id, version)
    - Add connection pooling and retry logic for Redis
    - Implement topic-based routing and wildcard subscriptions
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 15.2_

  - [ ]* 1.3 Write property tests for Event Bus
    - **Property 49: Event Routing by Type** - Validates: Requirements 11.1
    - **Property 50: Multiple Subscriber Support** - Validates: Requirements 11.2
    - **Property 51: Event Ordering Preservation** - Validates: Requirements 11.3
    - **Property 52: Event Envelope Metadata Completeness** - Validates: Requirements 11.4, 11.5, 11.6, 15.5
    - **Property 65: Event Envelope Validation** - Validates: Requirements 15.2

  - [x] 1.4 Set up PostgreSQL database schema
    - Create database initialization script with tables: `call_logs`, `transcript_logs`, `state_transition_logs`, `user_preferences`
    - Add indexes on `phone_number`, `session_id`, and `timestamp` columns
    - Implement connection pooling with SQLAlchemy
    - _Requirements: 9.1, 10.2, 10.3, 10.5_

  - [x] 1.5 Set up AWS S3 for audio storage
    - Configure S3 bucket with encryption (AES-256)
    - Implement upload/download utilities in `src/storage/s3_client.py`
    - Set up lifecycle policy for 90-day retention
    - _Requirements: 10.1_

  - [x] 1.6 Create configuration management system
    - Implement `src/config/system_config.py` to load from environment variables
    - Define configuration schema with latency budgets, module endpoints, retry policies
    - Add validation for required configuration fields
    - _Requirements: 15.1_

- [ ] 2. Checkpoint - Infrastructure validation
  - Verify Redis connection and pub/sub functionality
  - Verify PostgreSQL schema creation and queries
  - Verify S3 bucket access and file operations
  - Ensure all tests pass, ask the user if questions arise

### Phase 2: Core Pipeline Modules

- [-] 3. Implement Telephony Module
  - [x] 3.1 Create Telephony Module with Twilio integration
    - Implement `src/modules/telephony/telephony_module.py` with call initiation and reception
    - Set up WebSocket server for bidirectional audio streaming
    - Implement audio format conversion (μ-law to PCM16)
    - Publish `call_initiated`, `call_connected`, `call_ended`, `audio_input` events
    - Subscribe to `audio_output` events and stream to caller
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_

  - [ ]* 3.2 Write property tests for Telephony Module
    - **Property 1: WebSocket Establishment on Call Initiation** - Validates: Requirements 1.3
    - **Property 2: WebSocket Establishment on Call Reception** - Validates: Requirements 1.4
    - **Property 3: Call Lifecycle Event Publication** - Validates: Requirements 1.5, 1.6, 1.7
    - **Property 4: Audio Output Streaming** - Validates: Requirements 1.8

  - [ ] 3.3 Add Exotel provider support
    - Implement Exotel SDK integration in `src/modules/telephony/providers/exotel_provider.py`
    - Add provider abstraction layer to switch between Twilio and Exotel
    - _Requirements: 1.2_

- [-] 4. Implement Audio Processor Module
  - [x] 4.1 Create Audio Processor with noise reduction and VAD
    - Implement `src/modules/audio/audio_processor.py` with librosa and WebRTC VAD
    - Apply RNNoise for noise suppression (10ms per chunk)
    - Implement volume normalization to -20dB target
    - Implement VAD with 30ms sliding window and configurable aggressiveness
    - Detect speech start/end with 200ms latency target
    - Publish `processed_audio`, `speech_started`, `speech_ended` events
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7, 2.8, 2.9_

  - [x] 4.2 Implement barge-in detection
    - Monitor audio during TTS playback for agent speech
    - Publish `barge_in_detected` event within 200ms of detection
    - _Requirements: 2.5, 2.6_

  - [ ]* 4.3 Write property tests for Audio Processor
    - **Property 5: Noise Reduction Application** - Validates: Requirements 2.1
    - **Property 6: Volume Normalization** - Validates: Requirements 2.2
    - **Property 7: Speech Start Detection Latency** - Validates: Requirements 2.3, 12.2
    - **Property 8: Speech End Detection Latency** - Validates: Requirements 2.4, 12.3
    - **Property 9: Barge-In Detection Latency** - Validates: Requirements 2.5
    - **Property 10: Audio Processing Event Publication** - Validates: Requirements 2.6, 2.7, 2.8, 2.9

- [-] 5. Implement STT Module
  - [x] 5.1 Create STT Module with Google Cloud Speech-to-Text
    - Implement `src/modules/stt/stt_module.py` with streaming recognition
    - Configure language models for Hindi, Tamil, Kannada, Telugu, Marathi
    - Implement automatic language detection
    - Maintain persistent gRPC connections for low latency
    - Stream partial transcripts and publish `transcript_partial` events
    - Publish `transcript_final` events with language metadata and confidence scores
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10_

  - [ ]* 5.2 Write property tests for STT Module
    - **Property 11: Multi-Language STT Support** - Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    - **Property 12: STT Finalization Latency** - Validates: Requirements 3.6, 12.4
    - **Property 13: Partial Transcript Streaming** - Validates: Requirements 3.7
    - **Property 14: Automatic Language Detection** - Validates: Requirements 3.8
    - **Property 15: STT Event Publication** - Validates: Requirements 3.9, 3.10

  - [ ] 5.3 Add Azure Speech Services as fallback provider
    - Implement Azure STT integration in `src/modules/stt/providers/azure_stt.py`
    - Add provider switching logic with circuit breaker pattern
    - _Requirements: 3.6_

- [-] 6. Implement LLM Module
  - [x] 6.1 Create LLM Module with OpenAI GPT-4 integration
    - Implement `src/modules/llm/llm_module.py` with streaming API
    - Create prompt templates for each conversation state
    - Implement conversation context management (sliding window of last 3 turns)
    - Use Redis for context caching
    - Stream response tokens and publish `llm_response_token` events
    - Publish `llm_response_complete` event when generation finishes
    - Subscribe to `transcript_final` and `state_update` events
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [ ]* 6.2 Write property tests for LLM Module
    - **Property 16: LLM First Token Latency** - Validates: Requirements 4.1, 12.5
    - **Property 17: LLM Token Streaming** - Validates: Requirements 4.2
    - **Property 18: State Incorporation in LLM Context** - Validates: Requirements 4.3
    - **Property 19: Conversation Context Maintenance** - Validates: Requirements 4.4
    - **Property 20: LLM Event Publication** - Validates: Requirements 4.5, 4.6

  - [ ] 6.2 Add cultural localization to LLM prompts
    - Implement "ji" suffix appending for names
    - Add Indian phone number and currency formatting
    - Create culturally appropriate greetings for each language
    - _Requirements: 13.1, 13.2, 13.3, 13.5_

- [-] 7. Implement State Machine Module
  - [x] 7.1 Create State Machine with deterministic transitions
    - Implement `src/modules/state/state_machine.py` using python-statemachine library
    - Define states: greeting, awaiting_confirmation, clarification, confirmed, rejected, escalate
    - Implement transition logic based on intent detection from transcripts
    - Track clarification attempts and escalate after 3 attempts
    - Persist state to Redis for recovery
    - Publish `state_update` events on every transition
    - Subscribe to `call_connected`, `transcript_final`, `llm_response_complete` events
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_

  - [ ]* 7.2 Write property tests for State Machine
    - **Property 21: State Machine Initialization** - Validates: Requirements 5.1
    - **Property 22: Greeting to Awaiting Confirmation Transition** - Validates: Requirements 5.2
    - **Property 23: Intent-Based State Transitions** - Validates: Requirements 5.3, 5.4
    - **Property 24: Escalation on Max Clarifications** - Validates: Requirements 5.5
    - **Property 25: Single State Invariant** - Validates: Requirements 5.6
    - **Property 26: State Transition Event Publication** - Validates: Requirements 5.7

- [-] 8. Implement TTS Module
  - [x] 8.1 Create TTS Module with Google Cloud Text-to-Speech
    - Implement `src/modules/tts/tts_module.py` with streaming synthesis
    - Configure voice profiles for each language (hi-IN, ta-IN, kn-IN, te-IN, mr-IN)
    - Implement audio caching for common phrases
    - Stream audio chunks and publish `audio_output` events
    - Publish `tts_playback_started` and `tts_playback_stopped` events
    - Subscribe to `llm_response_token`, `state_update`, `barge_in_detected` events
    - Implement barge-in handling to stop playback within 200ms
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 16.1, 16.2, 16.4_

  - [ ]* 8.2 Write property tests for TTS Module
    - **Property 27: Language-Matched TTS Synthesis** - Validates: Requirements 6.1
    - **Property 28: TTS First Chunk Latency** - Validates: Requirements 6.2, 12.6
    - **Property 29: TTS Audio Streaming** - Validates: Requirements 6.3
    - **Property 30: Multi-Language TTS Support** - Validates: Requirements 6.4, 6.5, 6.6, 6.7, 6.8
    - **Property 31: Pre-Rendered Audio Cache Usage** - Validates: Requirements 6.9
    - **Property 32: TTS Event Publication** - Validates: Requirements 6.10
    - **Property 66: Barge-In TTS Interruption Latency** - Validates: Requirements 16.1, 16.2

- [ ] 9. Checkpoint - Core pipeline validation
  - Test complete audio flow: Telephony → Audio → STT → LLM → State → TTS → Telephony
  - Verify latency budgets for each module
  - Ensure all tests pass, ask the user if questions arise

### Phase 3: Supporting Modules

- [ ] 10. Implement Dashboard Module
  - [ ] 10.1 Create Dashboard backend with WebSocket server
    - Implement `src/modules/dashboard/dashboard_module.py` with FastAPI and WebSocket support
    - Subscribe to `call_connected`, `transcript_final`, `state_update`, `call_ended` events
    - Aggregate call data and push updates to WebSocket clients within 500ms
    - Maintain active call list with real-time updates
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

  - [ ] 10.2 Create Dashboard frontend with React
    - Build React app in `src/modules/dashboard/frontend/` with WebSocket client
    - Display grid view of active calls with live transcripts
    - Show state indicators, confidence scores, and call duration
    - Implement language indicator and color-coded state display
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 10.3 Write property tests for Dashboard Module
    - **Property 33: Dashboard Active Call Display** - Validates: Requirements 7.1
    - **Property 34: Dashboard Live Transcript Display** - Validates: Requirements 7.2
    - **Property 35: Dashboard State and Metadata Display** - Validates: Requirements 7.3, 7.4, 7.5, 7.6

- [ ] 11. Implement Call Controller Module
  - [x] 11.1 Create Call Controller with retry logic
    - Implement `src/modules/call_controller/call_controller.py` with Celery for task scheduling
    - Define retry policies for no_answer, dropped, and error scenarios
    - Implement exponential backoff calculation
    - Schedule retries using Celery delayed tasks
    - Publish `retry_scheduled` events
    - Subscribe to `call_ended` and `state_update` events
    - Implement retry decision matrix based on end reason and final state
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 18.1_

  - [ ]* 11.2 Write property tests for Call Controller
    - **Property 36: No-Answer Retry Scheduling** - Validates: Requirements 8.1, 8.6
    - **Property 37: Dropped Call Retry Scheduling** - Validates: Requirements 8.2, 8.6
    - **Property 38: Maximum Retry Attempts** - Validates: Requirements 8.3
    - **Property 39: No Retry for Terminal States** - Validates: Requirements 8.4, 8.5
    - **Property 40: Retry Event Publication** - Validates: Requirements 8.7
    - **Property 71: Retry Scheduling for Dropped Non-Terminal Calls** - Validates: Requirements 18.1

- [ ] 12. Implement Session Store Module
  - [x] 12.1 Create Session Store with PostgreSQL and Redis caching
    - Implement `src/modules/session_store/session_store.py` with SQLAlchemy ORM
    - Create methods for storing/retrieving user preferences by phone number
    - Implement Redis caching layer with 24-hour TTL
    - Implement write-through cache updates
    - Publish `preferences_loaded` events
    - Subscribe to `call_connected` and `call_ended` events
    - Track language preferences, interaction patterns, and call statistics
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 17.4, 18.4_

  - [ ]* 12.2 Write property tests for Session Store
    - **Property 41: Preference Storage Round-Trip** - Validates: Requirements 9.1, 9.2
    - **Property 42: Preference Retrieval on Call Start** - Validates: Requirements 9.3, 9.5
    - **Property 43: Preference Persistence on Call End** - Validates: Requirements 9.4
    - **Property 70: Stored Preference Language Initialization** - Validates: Requirements 17.4
    - **Property 74: Session Data Preservation Across Retries** - Validates: Requirements 18.4

- [ ] 13. Implement Logger Module
  - [x] 13.1 Create Logger with comprehensive audit trail
    - Implement `src/modules/logger/logger_module.py` with wildcard event subscription
    - Record all events to PostgreSQL with structured logging
    - Implement audio recording to S3 with WAV format (16kHz, mono)
    - Create batch insert logic for transcript logs (every 5 seconds)
    - Implement immediate writes for call lifecycle events
    - Store complete call logs, transcript logs, and state transition logs
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 18.2_

  - [ ]* 13.2 Write property tests for Logger Module
    - **Property 44: Complete Audio Recording** - Validates: Requirements 10.1
    - **Property 45: Transcript Logging with Timestamps** - Validates: Requirements 10.2
    - **Property 46: State Transition Logging** - Validates: Requirements 10.3
    - **Property 47: Session Association for All Logs** - Validates: Requirements 10.4
    - **Property 48: Log Persistence and Retrieval** - Validates: Requirements 10.5
    - **Property 72: Drop Reason Logging** - Validates: Requirements 18.2

- [ ] 14. Checkpoint - Supporting modules validation
  - Verify Dashboard displays active calls correctly
  - Test retry scheduling for different scenarios
  - Verify preference storage and retrieval
  - Confirm complete audit trail logging
  - Ensure all tests pass, ask the user if questions arise

### Phase 4: Integration and Cross-Cutting Concerns

- [ ] 15. Implement streaming data flow optimizations
  - [ ] 15.1 Optimize pipeline for streaming without buffering
    - Review all modules to ensure chunk-based processing
    - Remove any buffering that increases latency
    - Implement backpressure handling for slow consumers
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

  - [ ]* 15.2 Write property tests for streaming behavior
    - **Property 60: Audio Chunk Streaming Without Buffering** - Validates: Requirements 14.1
    - **Property 61: Transcript Streaming Without Sentence Completion** - Validates: Requirements 14.2
    - **Property 62: LLM Token Streaming Without Response Completion** - Validates: Requirements 14.3
    - **Property 63: TTS Chunk Streaming Without Synthesis Completion** - Validates: Requirements 14.4
    - **Property 64: No Latency-Increasing Buffering** - Validates: Requirements 14.5

- [ ] 16. Implement language detection and initialization
  - [ ] 16.1 Add language detection and preference handling
    - Implement default Hindi initialization for new calls
    - Add first utterance language detection logic
    - Implement language consistency within sessions
    - Load stored language preferences on call start
    - _Requirements: 17.1, 17.2, 17.3, 17.4_

  - [ ]* 16.2 Write property tests for language handling
    - **Property 58: Language Consistency Within Session** - Validates: Requirements 13.4, 17.3
    - **Property 59: Culturally Appropriate Greetings** - Validates: Requirements 13.5
    - **Property 68: Default Language Selection** - Validates: Requirements 17.1
    - **Property 69: First Utterance Language Detection** - Validates: Requirements 17.2

- [ ] 17. Implement barge-in handling across modules
  - [ ] 17.1 Integrate barge-in detection with STT and TTS
    - Ensure Audio Processor publishes barge_in_detected events
    - Verify TTS Module stops playback within 200ms
    - Verify STT Module processes new speech immediately
    - _Requirements: 16.1, 16.2, 16.3_

  - [ ]* 17.2 Write property test for barge-in processing
    - **Property 67: Barge-In STT Processing** - Validates: Requirements 16.3

- [ ] 18. Implement call drop recovery
  - [ ] 18.1 Add context restoration for retry calls
    - Implement context loading in State Machine for retry attempts
    - Restore conversation history, detected language, and clarification count
    - Ensure Session Store preserves data across drops
    - _Requirements: 18.3, 18.4_

  - [ ]* 18.2 Write property test for context restoration
    - **Property 73: Context Restoration on Retry** - Validates: Requirements 18.3

- [ ] 19. Implement error handling and recovery
  - [ ] 19.1 Add error handling across all modules
    - Implement exponential backoff retry for transient network errors
    - Add circuit breaker pattern for external APIs
    - Implement validation error handling with detailed logging
    - Add resource exhaustion monitoring and backpressure
    - Implement business logic error escalation
    - Create standardized error event schema
    - _Requirements: 11.7, 15.2_

  - [ ]* 19.2 Write property test for module communication isolation
    - **Property 53: Module Communication Isolation** - Validates: Requirements 11.7

- [ ] 20. Implement cultural localization features
  - [ ]* 20.1 Write property tests for localization
    - **Property 55: Name Suffix Localization** - Validates: Requirements 13.1
    - **Property 56: Indian Phone Number Formatting** - Validates: Requirements 13.2
    - **Property 57: Indian Currency Formatting** - Validates: Requirements 13.3

- [ ] 21. Checkpoint - Integration validation
  - Run end-to-end integration tests for all scenarios
  - Verify error handling and recovery mechanisms
  - Test barge-in handling across modules
  - Ensure all tests pass, ask the user if questions arise

### Phase 5: End-to-End Testing and Performance Validation

- [ ] 22. Implement integration tests
  - [ ] 22.1 Create integration test suite
    - Write test for happy path: complete call with confirmation
    - Write test for clarification flow
    - Write test for barge-in scenario
    - Write test for language switch between calls
    - Write test for retry flow after call drop
    - Write test for escalation after max clarifications
    - Set up test fixtures with mocked external APIs
    - _Requirements: All requirements_

- [ ] 23. Implement end-to-end latency validation
  - [ ]* 23.1 Write property test for end-to-end latency
    - **Property 54: End-to-End Latency Budget** - Validates: Requirements 12.1
    - Test with integration test setup and real/mocked services
    - Measure latency from speech_ended to first audio_output

- [ ] 24. Implement performance testing
  - [ ] 24.1 Create load testing suite
    - Implement load test simulating 100 concurrent calls
    - Measure P50, P95, P99 latency for each pipeline stage
    - Create stress test to identify system breaking point
    - Implement 24-hour soak test for memory leak detection
    - Set up performance monitoring dashboard
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [ ] 25. Checkpoint - Performance validation
  - Verify P95 latency < 1800ms under load
  - Confirm no memory leaks in soak test
  - Validate graceful degradation under stress
  - Ensure all tests pass, ask the user if questions arise

### Phase 6: Deployment and Monitoring

- [ ] 26. Create deployment infrastructure
  - [ ] 26.1 Create Docker containers for all modules
    - Write Dockerfiles for each module
    - Create docker-compose.yml for local development
    - Set up multi-stage builds for optimized images
    - _Requirements: All requirements_

  - [ ] 26.2 Create Kubernetes deployment manifests
    - Write K8s deployments for each module with resource limits
    - Create services for inter-module communication
    - Set up ConfigMaps and Secrets for configuration
    - Implement horizontal pod autoscaling based on CPU/memory
    - Create ingress for Dashboard and webhooks
    - _Requirements: All requirements_

  - [ ] 26.3 Set up CI/CD pipeline
    - Create GitHub Actions workflow for automated testing
    - Implement unit test stage (< 5 minutes)
    - Implement property test stage (< 15 minutes)
    - Implement integration test stage (< 10 minutes)
    - Add Docker image building and pushing
    - Implement canary deployment strategy
    - _Requirements: All requirements_

- [ ] 27. Implement monitoring and observability
  - [ ] 27.1 Set up metrics collection
    - Implement Prometheus metrics exporters in all modules
    - Track latency metrics (P50, P95, P99) for each pipeline stage
    - Track error rates by type and module
    - Track resource utilization (CPU, memory, connections)
    - Track business metrics (call success rate, escalation rate)
    - _Requirements: All requirements_

  - [ ] 27.2 Set up alerting
    - Create Grafana dashboards for system monitoring
    - Configure alerts for critical issues (error rate > 5%, latency P95 > 2500ms)
    - Configure alerts for high priority issues (error rate > 2%, resource > 85%)
    - Configure alerts for medium priority issues (error rate > 1%, latency P95 > 2000ms)
    - Set up PagerDuty integration for critical alerts
    - _Requirements: All requirements_

  - [ ] 27.3 Set up distributed tracing
    - Implement OpenTelemetry instrumentation across all modules
    - Set up Jaeger for trace collection and visualization
    - Add trace context propagation through Event Bus
    - Create trace-based latency analysis tools
    - _Requirements: 12.1_

- [ ] 28. Create operational documentation
  - [ ] 28.1 Write deployment and operations guide
    - Document deployment procedures
    - Create runbooks for common issues
    - Document monitoring and alerting setup
    - Create troubleshooting guide
    - Document scaling procedures
    - _Requirements: All requirements_

- [ ] 29. Final checkpoint - Production readiness
  - Verify all modules deployed and healthy
  - Confirm monitoring and alerting operational
  - Run smoke tests in staging environment
  - Review security configurations
  - Ensure all tests pass, ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Checkpoints ensure incremental validation at key milestones
- The implementation uses Python as the primary language with FastAPI for web services
- External services (Twilio, Google Cloud STT/TTS, OpenAI) require API credentials
- Local development uses Docker Compose with mocked external services
- Production deployment uses Kubernetes with auto-scaling
