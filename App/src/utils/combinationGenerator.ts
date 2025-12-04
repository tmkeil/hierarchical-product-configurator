import { Group } from '../types/mapping';

/**
 * Generiert alle Kombinationen für group_position String
 * Berücksichtigt variable Code-Längen!
 * 
 * Beispiel:
 * - Gruppe 1, Position 1: Codes [A, AT]
 * - Gruppe 1, Position 2: Codes [W, T]
 * 
 * Ergebnis: ["1:1=A,1:2=W", "1:1=A,1:2=T", "1:1=AT,1:3=W", "1:1=AT,1:3=T"]
 */
export function generateCombinationsForPreview(groups: Group[]): string[] {
  if (groups.length === 0) return [];

  // Für jede Gruppe: Sammle alle möglichen Kombinationen mit dynamischen Positionen
  const allGroupCombinations: string[][] = [];

  for (const group of groups) {
    if (group.positions.length === 0) continue;

    // Generiere alle Kombinationen für diese Gruppe
    const combinations = generateGroupCombinations(group);
    allGroupCombinations.push(combinations);
  }

  if (allGroupCombinations.length === 0) return [];

  // Kartesisches Produkt über alle Gruppen
  const cartesianProduct = (arrays: string[][]): string[][] => {
    return arrays.reduce((acc, curr) =>
      acc.flatMap(a => curr.map(c => [...a, c])),
      [[]] as string[][]
    );
  };

  const allCombinations = cartesianProduct(allGroupCombinations);
  
  // Kombiniere die Teile mit ","
  return allCombinations.map(parts => parts.join(','));
}

/**
 * Generiert alle Kombinationen für eine einzelne Gruppe
 */
function generateGroupCombinations(group: Group): string[] {
  if (group.positions.length === 0) return [];

  // Sortiere Positionen nach Index
  const sortedPositions = [...group.positions].sort((a, b) => a.positionIndex - b.positionIndex);

  // Rekursiv alle Kombinationen generieren
  const generateRecursive = (
    positionIndex: number,
    currentTypecodePos: number,
    path: string[]
  ): string[] => {
    if (positionIndex >= sortedPositions.length) {
      return [path.join(',')];
    }

    const position = sortedPositions[positionIndex];
    const results: string[] = [];

    for (const code of position.codes) {
      const segment = `${group.groupNumber}:${currentTypecodePos}=${code.value}`;
      const nextTypecodePos = currentTypecodePos + code.value.length;
      
      const childResults = generateRecursive(
        positionIndex + 1,
        nextTypecodePos,
        [...path, segment]
      );
      
      results.push(...childResults);
    }

    return results;
  };

  return generateRecursive(0, 1, []);
}
