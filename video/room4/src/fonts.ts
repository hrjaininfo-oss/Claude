import { loadFont } from '@remotion/fonts';
import { staticFile } from 'remotion';

// Fonts are bundled in /public/fonts (SIL OFL) so renders look identical on every machine.
export const FONT_TITLE = 'SpecialElite'; // typewriter / horror titles
export const FONT_HAND = 'CaveatBold'; // handwriting on the photo
export const FONT_SUB = 'InterSub'; // subtitles

loadFont({ family: FONT_TITLE, url: staticFile('fonts/SpecialElite.woff2'), weight: '400' });
loadFont({ family: FONT_HAND, url: staticFile('fonts/Caveat-Bold.woff2'), weight: '700' });
loadFont({ family: FONT_SUB, url: staticFile('fonts/Inter-SemiBold.woff2'), weight: '600' });
loadFont({ family: FONT_SUB, url: staticFile('fonts/Inter-ExtraBold.woff2'), weight: '800' });
