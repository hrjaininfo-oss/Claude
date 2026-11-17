/** Character designs — colours and features for the three friends. */
export type CharId = 'rahul' | 'karan' | 'vikram';

export type Look = {
  skin: string;
  skinShadow: string;
  skinLight: string;
  lip: string;
  hair: string;
  hairStyle: 'side' | 'curly' | 'oiled';
  iris: string;
  brow: string;
  top: string; // main garment
  topShadow: string;
  topDetail: string;
  under?: string; // t-shirt under open shirt
  pants: string;
  pantsShadow: string;
  shoes: string;
  mustache?: boolean;
  stubble?: boolean;
  glasses?: boolean;
  shawl?: string;
  kurta?: boolean;
  check?: boolean; // checked shirt pattern
  hoodie?: boolean;
  jaw: number; // 0 narrow … 1 broad
};

export const LOOKS: Record<CharId, Look> = {
  rahul: {
    skin: '#c58a5f',
    skinShadow: '#8a5634',
    skinLight: '#e2ad82',
    lip: '#8e4f3c',
    hair: '#151112',
    hairStyle: 'side',
    iris: '#3b2416',
    brow: '#1a1312',
    top: '#2c3e63',
    topShadow: '#18233b',
    topDetail: '#d9dde6',
    pants: '#2e3a52',
    pantsShadow: '#1b2333',
    shoes: '#e9e7e1',
    stubble: true,
    hoodie: true,
    jaw: 0.55,
  },
  karan: {
    skin: '#d9a77c',
    skinShadow: '#a06e4a',
    skinLight: '#f0c49c',
    lip: '#a45b4a',
    hair: '#2a1b12',
    hairStyle: 'curly',
    iris: '#4a2e1a',
    brow: '#2a1b12',
    top: '#8c2f2b',
    topShadow: '#541a18',
    topDetail: '#2b0f0e',
    under: '#c9c6bf',
    pants: '#8d7b5a',
    pantsShadow: '#5f523b',
    shoes: '#4b2e1c',
    glasses: true,
    check: true,
    jaw: 0.75,
  },
  vikram: {
    skin: '#b38262',
    skinShadow: '#6f4a35',
    skinLight: '#d3a584',
    lip: '#7a4636',
    hair: '#0d0a0a',
    hairStyle: 'oiled',
    iris: '#1c120c',
    brow: '#0d0a0a',
    top: '#e6dcc4',
    topShadow: '#a69a80',
    topDetail: '#c9b994',
    pants: '#ece6d6',
    pantsShadow: '#b0a690',
    shoes: '#5a3a1c',
    mustache: true,
    shawl: '#5b3520',
    kurta: true,
    jaw: 0.65,
  },
};

export const SPEAKER_COLOR: Record<string, string> = {
  vikram: '#ffb347',
  rahul: '#8fd3ff',
  karan: '#b9f18c',
  ghost: '#d8d2e8',
};
