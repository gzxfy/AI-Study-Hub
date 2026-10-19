export function topicColor(color) {
  return /^#[0-9a-f]{6}$/i.test(color) ? color : '#087f65';
}
