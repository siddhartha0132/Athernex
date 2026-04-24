import { useEffect, useRef, useState } from 'react'
import { io, Socket } from 'socket.io-client'

const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

export function useSocket() {
  const socketRef = useRef<Socket | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('vyapaarsetu_token')
    
    socketRef.current = io(SOCKET_URL, {
      auth: { token },
      transports: ['websocket'],
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    })

    socketRef.current.on('connect', () => {
      console.log('Socket connected')
      setConnected(true)
    })

    socketRef.current.on('disconnect', () => {
      console.log('Socket disconnected')
      setConnected(false)
    })

    socketRef.current.on('connect_error', (error) => {
      console.error('Socket connection error:', error)
      setConnected(false)
    })

    return () => {
      socketRef.current?.disconnect()
    }
  }, [])

  return { socket: socketRef.current, connected }
}