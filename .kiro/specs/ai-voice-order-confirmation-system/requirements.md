# Requirements Document

## Introduction

This document specifies requirements for a modular AI voice operating system that handles real-time phone calls with delivery agents to confirm orders in Hindi and regional Indian languages. The system uses a pipeline-based architecture with 10 interconnected modules communicating via an event bus, with strict latency requirements to ensure natural conversation flow.

## Glossary

- **System**: The complete AI voice order confirmation system
- **Telephony_Module**: Component responsible for initiating/receiving calls and streaming audio
- **Audio_Processor**: Component handling noise reduction, normalization, and voice activity detection
- **VAD**: Voice Activity Detection - detects when speech starts and ends
- **STT_Module**: Speech-to-Text module for real-time transcription
- **LLM_Module**: Large Language Model integration for processing conversation context
- **State_Machine**: Conversation state management component tracking call stages
- **TTS_Module**: Text-to-Speech synthesis component
- **Dashboard**: Real-time monitoring interface for active calls
- **Call_Controller**: Component managing retry logic and call lifecycle
- **Session_Store**: Persistent storage for user preferences and history
- **Logger**: Component for recording audio and storing transcripts
- **Event_Bus**: Central message broker for inter-module communication
- **Event_Envelope**: Standardized message format for event bus communication
- **Delivery_Agent**: The person receiving the confirmation call
- **Barge_In**: When a speaker interrupts while the system is speaking
- **Call_Session**: A single phone call instance with associated state

## Requirements

### Requirement 1: Telephony Integration

**User Story:** As a system operator, I want to initiate and receive phone calls through telephony providers, so that the system can communicate with delivery agents.

#### Acceptance Criteria

1. THE Telephony_Module SHALL support integration with Twilio telephony provider
2. THE Telephony_Module SHALL support integration with Exotel telephony provider
3. WHEN a call is initiated, THE Telephony_Module SHALL establish a WebSocket connection for audio streaming
4. WHEN a call is received, THE Telephony_Module SHALL accept the connection and establish bidirectional audio streaming
5. THE Telephony_Module SHALL publish call_initiated events to the Event_Bus
6. THE Telephony_Module SHALL publish call_connected events to the Event_Bus
7. THE Telephony_Module SHALL publish call_ended events to the Event_Bus
8. THE Telephony_Module SHALL consume audio_output events from the Event_Bus and stream audio to the active call

### Requirement 2: Audio Processing and Voice Activity Detection

**User Story:** As a system operator, I want clean audio with accurate speech detection, so that transcription quality is maximized.

#### Acceptance Criteria

1. WHEN audio is received, THE Audio_Processor SHALL apply noise reduction
2. WHEN audio is received, THE Audio_Processor SHALL normalize volume levels
3. WHEN speech begins, THE Audio_Processor SHALL detect the start within 200ms
4. WHEN speech ends, THE Audio_Processor SHALL detect the end within 200ms
5. WHEN the system is speaking and the Delivery_Agent speaks, THE Audio_Processor SHALL detect barge-in within 200ms
6. WHEN barge-in is detected, THE Audio_Processor SHALL publish barge_in_detected events to the Event_Bus
7. THE Audio_Processor SHALL publish processed_audio events to the Event_Bus
8. THE Audio_Processor SHALL publish speech_started events to the Event_Bus
9. THE Audio_Processor SHALL publish speech_ended events to the Event_Bus

### Requirement 3: Multi-Language Speech Recognition

**User Story:** As a delivery agent, I want to speak in my preferred Indian language, so that I can communicate naturally.

#### Acceptance Criteria

1. THE STT_Module SHALL transcribe speech in Hindi
2. THE STT_Module SHALL transcribe speech in Tamil
3. THE STT_Module SHALL transcribe speech in Kannada
4. THE STT_Module SHALL transcribe speech in Telugu
5. THE STT_Module SHALL transcribe speech in Marathi
6. WHEN processed audio is received, THE STT_Module SHALL produce a final transcript within 400ms of speech end
7. THE STT_Module SHALL stream partial transcripts as speech continues
8. THE STT_Module SHALL detect the spoken language automatically
9. THE STT_Module SHALL publish transcript_partial events to the Event_Bus
10. THE STT_Module SHALL publish transcript_final events to the Event_Bus with detected language metadata

### Requirement 4: Language Model Integration

**User Story:** As a system operator, I want intelligent response generation based on conversation context, so that calls feel natural and handle varied agent responses.

#### Acceptance Criteria

1. WHEN a final transcript is received, THE LLM_Module SHALL generate a response within 800ms for the first token
2. THE LLM_Module SHALL stream response tokens as they are generated
3. THE LLM_Module SHALL incorporate conversation state from the State_Machine when generating responses
4. THE LLM_Module SHALL maintain conversation context across multiple turns within a Call_Session
5. THE LLM_Module SHALL publish llm_response_token events to the Event_Bus
6. THE LLM_Module SHALL publish llm_response_complete events to the Event_Bus
7. THE LLM_Module SHALL consume transcript_final events from the Event_Bus
8. THE LLM_Module SHALL consume state_update events from the Event_Bus

### Requirement 5: Conversation State Management

**User Story:** As a system operator, I want deterministic conversation flow tracking, so that the system knows what stage each call is in.

#### Acceptance Criteria

1. WHEN a call begins, THE State_Machine SHALL initialize state to greeting stage
2. THE State_Machine SHALL transition from greeting to awaiting_confirmation stage after initial greeting
3. THE State_Machine SHALL transition to confirmed stage when confirmation is detected
4. THE State_Machine SHALL transition to rejected stage when rejection is detected
5. THE State_Machine SHALL transition to escalate stage when the conversation cannot be resolved
6. THE State_Machine SHALL maintain exactly one state per Call_Session
7. THE State_Machine SHALL publish state_update events to the Event_Bus on every transition
8. THE State_Machine SHALL consume transcript_final events to determine state transitions
9. THE State_Machine SHALL consume llm_response_complete events to track conversation progress

### Requirement 6: Multi-Language Speech Synthesis

**User Story:** As a delivery agent, I want to hear responses in the same language I'm speaking, so that communication is clear.

#### Acceptance Criteria

1. WHEN a response is received, THE TTS_Module SHALL synthesize audio in the detected language
2. THE TTS_Module SHALL produce the first audio chunk within 300ms of receiving text
3. THE TTS_Module SHALL stream audio chunks as synthesis continues
4. THE TTS_Module SHALL support Hindi speech synthesis
5. THE TTS_Module SHALL support Tamil speech synthesis
6. THE TTS_Module SHALL support Kannada speech synthesis
7. THE TTS_Module SHALL support Telugu speech synthesis
8. THE TTS_Module SHALL support Marathi speech synthesis
9. WHERE pre-rendered audio clips are available, THE TTS_Module SHALL use them instead of synthesizing
10. THE TTS_Module SHALL publish audio_output events to the Event_Bus
11. THE TTS_Module SHALL consume llm_response_token events from the Event_Bus

### Requirement 7: Real-Time Call Monitoring

**User Story:** As a system operator, I want to monitor active calls in real-time, so that I can observe system performance and intervene if needed.

#### Acceptance Criteria

1. THE Dashboard SHALL display all active Call_Sessions
2. THE Dashboard SHALL display live transcripts for each Call_Session
3. THE Dashboard SHALL display detected intents for each Call_Session
4. THE Dashboard SHALL display confidence scores for transcription and intent detection
5. THE Dashboard SHALL display current state for each Call_Session
6. THE Dashboard SHALL update displays within 500ms of receiving new data
7. THE Dashboard SHALL establish WebSocket connections for real-time updates
8. THE Dashboard SHALL consume transcript_final events from the Event_Bus
9. THE Dashboard SHALL consume state_update events from the Event_Bus

### Requirement 8: Call Retry and Lifecycle Management

**User Story:** As a system operator, I want automatic retry logic for failed calls, so that delivery agents are reached reliably.

#### Acceptance Criteria

1. WHEN a call receives no answer, THE Call_Controller SHALL schedule a retry after 2 hours
2. WHEN a call is dropped, THE Call_Controller SHALL schedule a retry after 30 minutes
3. THE Call_Controller SHALL attempt a maximum of 3 retries for no-answer scenarios
4. WHEN a call reaches confirmed state, THE Call_Controller SHALL not schedule any retries
5. WHEN a call reaches rejected state, THE Call_Controller SHALL not schedule any retries
6. THE Call_Controller SHALL use exponential backoff for subsequent retry attempts
7. THE Call_Controller SHALL publish retry_scheduled events to the Event_Bus
8. THE Call_Controller SHALL consume call_ended events from the Event_Bus
9. THE Call_Controller SHALL consume state_update events from the Event_Bus

### Requirement 9: User Preference Persistence

**User Story:** As a delivery agent, I want the system to remember my language preference, so that subsequent calls start in my preferred language.

#### Acceptance Criteria

1. THE Session_Store SHALL store language preference keyed by phone number
2. THE Session_Store SHALL store past interaction patterns keyed by phone number
3. WHEN a call begins, THE Session_Store SHALL retrieve stored preferences for the phone number
4. WHEN a call ends, THE Session_Store SHALL persist updated preferences
5. THE Session_Store SHALL publish preferences_loaded events to the Event_Bus
6. THE Session_Store SHALL consume call_connected events from the Event_Bus
7. THE Session_Store SHALL consume call_ended events from the Event_Bus

### Requirement 10: Audit Trail and Recording

**User Story:** As a compliance officer, I want complete records of all calls, so that interactions can be reviewed and analyzed.

#### Acceptance Criteria

1. THE Logger SHALL record complete audio for every Call_Session
2. THE Logger SHALL store transcripts with timestamps for every utterance
3. THE Logger SHALL log all state transitions with timestamps
4. THE Logger SHALL associate all logs with the corresponding Call_Session identifier
5. THE Logger SHALL persist logs to durable storage
6. THE Logger SHALL consume all events from the Event_Bus for logging purposes

### Requirement 11: Event-Driven Communication Architecture

**User Story:** As a system architect, I want all modules to communicate through a central event bus, so that the system is loosely coupled and scalable.

#### Acceptance Criteria

1. THE Event_Bus SHALL route events from publishers to subscribers based on event type
2. THE Event_Bus SHALL support multiple subscribers for a single event type
3. THE Event_Bus SHALL deliver events in the order they were published
4. THE Event_Bus SHALL include timestamp metadata in every Event_Envelope
5. THE Event_Bus SHALL include source module identifier in every Event_Envelope
6. THE Event_Bus SHALL include Call_Session identifier in every Event_Envelope
7. THE System SHALL prohibit direct API calls between modules

### Requirement 12: End-to-End Latency Performance

**User Story:** As a delivery agent, I want natural conversation flow without awkward pauses, so that the call feels like talking to a human.

#### Acceptance Criteria

1. THE System SHALL achieve total perceived latency of less than 1800ms from speech end to audio response start
2. WHEN speech ends, THE Audio_Processor SHALL detect it within 200ms
3. WHEN speech ends, THE STT_Module SHALL produce final transcript within 400ms
4. WHEN transcript is received, THE LLM_Module SHALL produce first token within 800ms
5. WHEN response text is received, THE TTS_Module SHALL produce first audio chunk within 300ms

### Requirement 13: Cultural Localization

**User Story:** As a delivery agent in India, I want culturally appropriate interactions, so that the conversation feels respectful and natural.

#### Acceptance Criteria

1. WHEN addressing a Delivery_Agent, THE System SHALL append "ji" suffix to names
2. THE System SHALL format phone numbers using Indian conventions
3. THE System SHALL format currency using Indian Rupee notation
4. WHEN a language is selected for a Call_Session, THE System SHALL maintain that language until call end
5. THE System SHALL use culturally appropriate greetings for the detected language

### Requirement 14: Streaming Data Flow

**User Story:** As a system architect, I want all data to stream through the pipeline, so that latency is minimized and responsiveness is maximized.

#### Acceptance Criteria

1. THE Audio_Processor SHALL stream processed audio chunks without buffering complete utterances
2. THE STT_Module SHALL stream partial transcripts without waiting for complete sentences
3. THE LLM_Module SHALL stream response tokens without waiting for complete responses
4. THE TTS_Module SHALL stream audio chunks without waiting for complete synthesis
5. THE System SHALL prohibit buffering that would increase end-to-end latency beyond specified limits

### Requirement 15: Module Interface Contracts

**User Story:** As a module developer, I want clearly defined input/output schemas, so that I can develop and test modules independently.

#### Acceptance Criteria

1. THE System SHALL define a schema for every event type published to the Event_Bus
2. THE System SHALL validate Event_Envelope structure before routing
3. THE System SHALL document events consumed by each module
4. THE System SHALL document events published by each module
5. THE System SHALL version all event schemas to support backward compatibility

### Requirement 16: Barge-In Handling

**User Story:** As a delivery agent, I want to interrupt the system when it's speaking, so that I can respond quickly without waiting.

#### Acceptance Criteria

1. WHEN barge-in is detected, THE System SHALL stop TTS playback within 200ms
2. WHEN barge-in is detected, THE System SHALL clear any queued audio output
3. WHEN barge-in is detected, THE STT_Module SHALL begin processing the new speech immediately
4. THE TTS_Module SHALL consume barge_in_detected events from the Event_Bus

### Requirement 17: Language Detection and Initialization

**User Story:** As a delivery agent, I want the system to automatically detect my language, so that I don't need to specify it explicitly.

#### Acceptance Criteria

1. WHEN a call begins and no stored preference exists, THE System SHALL use Hindi as the default language
2. WHEN the first utterance is transcribed, THE STT_Module SHALL detect the spoken language
3. WHEN language is detected, THE System SHALL use that language for all subsequent TTS in the Call_Session
4. WHERE a stored language preference exists, THE System SHALL initialize the Call_Session with that language

### Requirement 18: Call Drop Recovery

**User Story:** As a system operator, I want graceful handling of network issues, so that temporary problems don't result in lost confirmations.

#### Acceptance Criteria

1. WHEN a call is dropped before reaching confirmed or rejected state, THE Call_Controller SHALL schedule a retry
2. WHEN a call is dropped, THE Logger SHALL mark the Call_Session with drop reason
3. WHEN a retry call connects, THE State_Machine SHALL initialize with context from the previous attempt
4. THE System SHALL preserve Session_Store data across call drops and retries
