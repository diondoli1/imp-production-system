# Project Brief — IMP CNC Production Tracking Prototype

## Project name
IMP CNC Production Tracking Prototype

## Goal
Build a working demo of a digital production tracking system for IMP that shows how production tracking could work on a HAAS CNC machine using:
- a simulated CNC machine
- a tablet-based operator interface
- a supervisor dashboard
- AI-assisted analysis

## Why this exists
IMP currently uses a manual workflow:
- operators receive printed technical drawings
- operators write produced quantities on the printed drawing
- the drawing is later placed in a folder for management review
- scrap, downtime, alarms, and interruptions are not systematically logged

This prototype demonstrates how a digital workflow could replace that process.

## Real context
- IMP uses HAAS machines only
- machines are connected to a server for file transfer only
- no live machine data is currently consumed
- production orders for IMP are not tracked in SteelTrack
- IMP uses Monday.com mainly for orders and operator tasks
- operators write piece counts on technical drawings
- management wants both machine runtime tracking and piece-count tracking

## Prototype scope
This is a single-machine demo.
Machine ID:
`HAAS_VF2_01`

The prototype includes:
- CNC simulator
- backend API
- event engine
- SQLite database
- operator tablet UI
- supervisor dashboard
- WebSocket live updates
- AI analysis layer

The prototype excludes:
- real machine integration
- ERP integration
- multi-machine support
- Docker in v1
- predictive maintenance
- AI machine control

## Deployment model
- backend + DB + simulator run on local office PC
- tablet connects over local Wi-Fi
- tablet can display both operator view and dashboard
- internet dependence is acceptable
- AI uses internet access through the OpenAI API

## Design philosophy
The software should look industrial and professional, not futuristic.
It should feel like real factory software:
- clear
- high contrast
- simple
- touch-friendly
- low animation
- readable from a distance

## Main value demonstrated
1. Digital operator workflow
2. Real-time machine state visibility
3. Structured event logging
4. Scrap and interruption tracking
5. AI-assisted reason suggestion and analysis
6. A credible architecture for future expansion
