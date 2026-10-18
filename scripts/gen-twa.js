#!/usr/bin/env node
/**
 * Génère le projet Android (TWA) et la clé de signature de façon
 * entièrement non-interactive, à partir du manifeste PWA en ligne.
 * Utilisé par .github/workflows/build-apk.yml — ne pas lancer à la main
 * sans savoir ce que ça fait (ça écrase twa-manifest.json et le dossier
 * android/ généré).
 */
const path = require('path');
const fs = require('fs').promises;
const { existsSync } = require('fs');
const crypto = require('crypto');
const {
  TwaManifest, TwaGenerator, JdkHelper, KeyTool, Config, ConsoleLog,
} = require('@bubblewrap/core');

const MANIFEST_URL = process.env.PWA_MANIFEST_URL ||
  'https://coxewagen.github.io/predicteur-ligue1/manifest.webmanifest';
const PACKAGE_ID = process.env.TWA_PACKAGE_ID || 'com.coxewagen.predicteurligue1';
const TARGET_DIR = process.cwd();

// Mots de passe du keystore : usage perso (pas de distribution Play Store),
// donc pas besoin de secrets GitHub pour ça — valeurs fixes volontairement.
const KEYSTORE_PASSWORD = 'predicteurL1store';
const KEY_PASSWORD = 'predicteurL1key';

async function main() {
  const twaManifest = await TwaManifest.fromWebManifest(MANIFEST_URL);
  twaManifest.packageId = PACKAGE_ID;
  twaManifest.signingKey.path = path.join(TARGET_DIR, 'android.keystore');
  twaManifest.signingKey.alias = 'android';
  twaManifest.appVersionCode = parseInt(process.env.TWA_VERSION_CODE || '1', 10);
  twaManifest.appVersionName = twaManifest.appVersionCode.toString();

  const manifestFile = path.join(TARGET_DIR, 'twa-manifest.json');
  await twaManifest.saveToFile(manifestFile);

  const log = new ConsoleLog('gen-twa');
  const twaGenerator = new TwaGenerator();
  await twaGenerator.createTwaProject(TARGET_DIR, twaManifest, log);

  // manifest-checksum.txt : évite que `bubblewrap build` ne redemande une
  // confirmation interactive de mise à jour du projet.
  const manifestContents = await fs.readFile(manifestFile);
  const sum = crypto.createHash('sha1').update(manifestContents).digest('hex');
  await fs.writeFile(path.join(TARGET_DIR, 'manifest-checksum.txt'), sum);

  if (!existsSync(twaManifest.signingKey.path)) {
    const config = new Config(process.env.JAVA_HOME, process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT);
    const jdkHelper = new JdkHelper(process, config);
    const keytool = new KeyTool(jdkHelper, log);
    await keytool.createSigningKey({
      fullName: 'Hans',
      organizationalUnit: 'Predicteur Ligue 1',
      organization: 'Predicteur Ligue 1',
      country: 'FR',
      password: KEYSTORE_PASSWORD,
      keypassword: KEY_PASSWORD,
      alias: twaManifest.signingKey.alias,
      path: twaManifest.signingKey.path,
    });
    console.log('Clé de signature générée.');
  } else {
    console.log('Clé de signature existante réutilisée.');
  }

  console.log('Projet TWA prêt.');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
