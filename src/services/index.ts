import { logger } from '../lib/utils/logging'
import { ServiceFactory } from './factory/ServiceFactory'

export const services = ServiceFactory.getInstance({
  logger,
})
