import { ACT1 } from './act1';
import { ACT2 } from './act2';
import { ACT3 } from './act3';
import { Shot } from '../edit';

/** The full edit, in order. Each shot: absolute from/to (seconds) + incoming transition. */
export const SHOTS: Shot[] = [...ACT1, ...ACT2, ...ACT3];
