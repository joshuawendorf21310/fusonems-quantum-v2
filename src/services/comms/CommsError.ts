export class CommsError extends Error {
  statusCode?: number
  details?: unknown

  constructor(message: string, options: { statusCode?: number; details?: unknown } = {}) {
    super(message)
    this.name = "CommsError"
    this.statusCode = options.statusCode
    this.details = options.details
  }
}
