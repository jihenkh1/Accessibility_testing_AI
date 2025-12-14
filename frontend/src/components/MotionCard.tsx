import * as React from 'react'
import { motion, useReducedMotion, type Variants } from 'framer-motion'
import { cn } from './ui/utils'

type MotionCardProps = React.ComponentProps<typeof motion.div> & {
  variants?: Variants
}

const MotionCard = React.forwardRef<HTMLDivElement, MotionCardProps>(
  ({ className, children, ...props }, ref) => {
    const reduceMotion = useReducedMotion()
    const initial = { opacity: 0, y: reduceMotion ? 0 : 8 }
    const animate = { opacity: 1, y: 0 }
    const hover = reduceMotion ? undefined : { y: -2, transition: { duration: 0.2, ease: 'easeOut' } }

    return (
      <motion.div
        ref={ref}
        initial={initial}
        whileInView={animate}
        viewport={{ once: true, margin: '-10%' }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        whileHover={hover}
        className={cn('rounded-xl border border-border bg-card shadow-sm', className)}
        {...props}
      >
        {children}
      </motion.div>
    )
  }
)

MotionCard.displayName = 'MotionCard'

export default MotionCard
